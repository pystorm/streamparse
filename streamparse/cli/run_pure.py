"""
Run a pure Python topology without using Storm.

This is not at all intended to be used in production. It is very handy
for debugging though, since you can step through topology execution when
run pdb:

  python -m backports.pdb -m streamparse.cli.sparse run_pure -n TOPOLOGY -e ENV
"""

from __future__ import absolute_import, print_function

import time
import uuid
from argparse import RawDescriptionHelpFormatter
from collections import Counter, defaultdict, deque, namedtuple
from io import BytesIO
from traceback import print_exc

import ipdb
import pystorm.component
from pystorm.serializers.serializer import Serializer

from ..storm import BatchingBolt, Spout, TicklessBatchingBolt
from ..util import (
    get_config,
    get_env_config,
    get_topology_definition,
    get_topology_from_file,
    set_topology_serializer,
)
from .common import (
    add_ackers,
    add_config,
    add_debug,
    add_environment,
    add_name,
    add_options,
    add_override_name,
    add_workers,
    resolve_options,
)


class FakeSerializer(Serializer):
    """Serializer that does not actual serialize things

    :param Serializer: [description]
    :type Serializer: [type]
    """

    def __init__(self, input_stream, output_stream, reader_lock, writer_lock):
        self._reader_lock = reader_lock
        self._writer_lock = writer_lock
        self.input_stream = deque()
        self.output_stream = deque()

    def read_message(self, stream=None):
        """Pop a message off the left of the stream (default: input_stream)"""
        if stream is None:
            stream = self.input_stream
        try:
            message = stream.popleft()
        except IndexError:
            message = None
        return message

    def send_message(self, msg_dict, stream=None):
        """Put a message in the specified stream (default: output_stream"""
        if stream is None:
            stream = self.output_stream
        stream.append(msg_dict)


pystorm.component._SERIALIZERS["fake"] = FakeSerializer


TupleMetadata = namedtuple(
    "TupleMetadata", "id component stream anchors children values"
)


class FakeStorm(object):
    """A single-threaded pure Python implementation of Storm.

    This exists for testing and debugging purposes, and would be
    next to useless in production.
    """

    def __init__(self, topology_class, env_name, storm_options):
        name = storm_options["topology.name"]
        self.inputs = {}
        self.outputs = {}
        self.components = {}
        self.spouts = {}
        self.bolts = {}
        self.target_components = defaultdict(lambda: defaultdict(list))
        self.unacked_tuples = {}
        self.spout_pending = Counter()
        self.failed_tuples = {}
        self.start_time = 0
        self.end_time = -1
        self.emitted_counters = defaultdict(Counter)
        self.acked_counters = defaultdict(Counter)
        self.failed_counters = defaultdict(Counter)
        self.ignored_spouts = set()
        self.tick_freq = 1

        try:
            # Set parallelism based on env_name if necessary
            for spec in topology_class.specs:
                # TODO: Remove this unless we start actually using par
                if isinstance(spec.par, dict):
                    spec.par = spec.par.get(env_name)
                # create a single instance of the class represented by each spec
                if issubclass(spec.component_cls, TicklessBatchingBolt):
                    secs_between_batches = spec.component_cls.secs_between_batches
                    # Remove TicklessBatchingBolt from __mro__ to simplify life
                    spec.component_cls = type(
                        spec.component_cls.__name__,
                        (BatchingBolt,),
                        dict(vars(spec.component_cls)),
                    )
                    # convert secs_between_batches to ticks_between_batches
                    spec.component_cls.ticks_between_batches = secs_between_batches
                    storm_options["topology.tick.tuple.freq.secs"] = 1

                component = spec.component_cls(
                    input_stream=BytesIO(), output_stream=BytesIO(), serializer="fake"
                )
                self.components[spec.name] = component

                if isinstance(component, Spout):
                    self.spouts[spec.name] = component
                else:
                    self.bolts[spec.name] = component

                # Save streams for later for easier access
                self.inputs[spec.name] = spec.inputs
                self.outputs[spec.name] = spec.outputs

            # Initialize all components
            for task_id, (component_name, component) in enumerate(
                self.components.items()
            ):
                context = {
                    "topology.name": name,
                    "taskid": task_id,
                    "componentid": component_name,
                }
                sources = defaultdict(dict)
                if component_name not in self.target_components:
                    self.target_components[component_name] = defaultdict(list)
                for stream_id, grouping in self.inputs[component_name].items():
                    input_component = stream_id.componentId
                    input_stream = stream_id.streamId
                    input_fields = self.outputs[input_component][
                        input_stream
                    ].output_fields
                    sources[input_component][input_stream] = input_fields
                    self.target_components[input_component][input_stream].append(
                        component_name
                    )
                    # TODO: Handle grouping types if we ever start using par
                context["source->stream->fields"] = sources
                component._setup_component(storm_options, context)
                component.initialize(storm_options, context)
        except Exception as e:
            print_exc()
            ipdb.post_mortem()

    def emit(self, message, component_name):
        """Send tuple in message to all components that should receive it"""
        tup = message["tuple"]
        stream_name = message.get("stream", "default")
        # Spout emits have IDs and no anchors, bolts have optional anchors.
        # We handle this by making up a fake anchor for the spout tuples.
        if component_name in self.spouts:
            tup_id = message.get("id")
            expanded_id = "{}__{}__{}".format(component_name, stream_name, tup_id)
            anchors = [expanded_id]
            self.unacked_tuples[expanded_id] = TupleMetadata(
                tup_id, component_name, stream_name, [component_name], set(), tup
            )
            self.spout_pending[component_name] += 1
        else:
            anchors = message.get("anchors", [])
        if stream_name not in self.outputs[component_name]:
            raise RuntimeError(
                '"{}" is not a defined output stream for "{}". Did '
                'you forget to set "outputs"?'.format(stream_name, component_name)
            )
        # TODO: direct
        # TODO: need_task_ids
        output_command = {
            "comp": component_name,
            "stream": stream_name,
            "task": 0,
            "tuple": tup,
        }

        self.emitted_counters[component_name][stream_name] += 1

        for target_name in self.target_components[component_name][stream_name]:
            tup_id = uuid.uuid4().int
            output_command["id"] = tup_id
            target_component = self.components[target_name]
            target_component.serializer.send_message(
                output_command, stream=target_component.serializer.input_stream
            )
            self.unacked_tuples[tup_id] = TupleMetadata(
                tup_id, component_name, stream_name, anchors, set(), tup
            )
            for anchor in anchors:
                self.unacked_tuples[anchor].children.add(tup_id)

    def ack(self, tup_id):
        """Mark tuple as ACKed, and ACK anything further up the tree"""
        # Got an ACK for a failed tuple
        if tup_id not in self.unacked_tuples:
            print("Ignoring ack for unknown tuple: {}".format(tup_id))
            return
        tup_metadata = self.unacked_tuples[tup_id]
        self.acked_counters[tup_metadata.component][tup_metadata.stream] += 1
        num_acked = self.acked_counters[tup_metadata.component][tup_metadata.stream]
        if num_acked % 20 == 0:
            print(
                "Cumulative count of tuples acked for {}__{}: {}".format(
                    tup_metadata.component, tup_metadata.stream, num_acked
                )
            )
        for anchor in tup_metadata.anchors:
            # Tick tuples come from FakeStorm itself
            if anchor == "__system":
                continue
            # Send ack command to spouts
            elif anchor == tup_metadata.component:
                spout_obj = self.spouts[tup_metadata.component]
                # Stop ignoring spout output from previous sync
                self.ignored_spouts.discard(spout_obj.component_name)
                spout_obj.serializer.send_message(
                    {"command": "ack", "id": tup_id.split("__")[-1]},
                    stream=spout_obj.serializer.input_stream,
                )
                # Read command and call process
                self.read_and_process(spout_obj)
                self.spout_pending[spout_obj.component_name] -= 1
            else:
                # Anchor was already failed, so this whole tree is dead
                if anchor not in self.unacked_tuples:
                    continue
                tups_for_anchor = self.unacked_tuples[anchor].children
                tups_for_anchor.remove(tup_id)
                if not tups_for_anchor:
                    self.ack(anchor)
        del self.unacked_tuples[tup_id]

    def fail(self, tup_id):
        """Mark tuple as failed"""
        # Got a fail for something that already failed
        if tup_id not in self.unacked_tuples:
            print("Failing already failed tuple: ", tup_id)
            return
        # Follow tree up to spouts
        tup_metadata = self.unacked_tuples[tup_id]
        self.failed_counters[tup_metadata.component][tup_metadata.stream] += 1
        num_failed = self.failed_counters[tup_metadata.component][tup_metadata.stream]
        if num_failed % 20 == 0:
            print(
                "Cumulative count of tuples failed for {}__{}: {}".format(
                    tup_metadata.component, tup_metadata.stream, num_failed
                )
            )
        self.failed_tuples[tup_id] = tup_metadata
        for anchor in tup_metadata.anchors:
            # Send fail command to spouts
            if anchor == tup_metadata.component:
                spout_obj = self.spouts[tup_metadata.component]
                # Stop ignoring spout output from previous sync
                self.ignored_spouts.discard(spout_obj.component_name)
                spout_obj.serializer.send_message(
                    {"command": "fail", "id": tup_id},
                    stream=spout_obj.serializer.input_stream,
                )
                # Read command and call process
                self.read_and_process(spout_obj)
            else:
                self.fail(anchor)
        del self.unacked_tuples[tup_id]

    def read_and_process(self, component):
        """Read commands waiting for component and process them"""
        # Don't bother when there is nothing in the input stream
        if not component.serializer.input_stream:
            return
        component._run()
        message = component.serializer.read_message(
            stream=component.serializer.output_stream
        )
        while message is not None:
            command = message["command"]
            # Ignore output from ignored spouts
            if component.component_name in self.ignored_spouts:
                print(
                    "Ignoring unrequested output from spout {}: {}".format(
                        component.component_name, message
                    )
                )
            elif command == "log":
                print(message["msg"])
            # Send output to appropriate downstream bolts
            elif command == "emit":
                self.emit(message, component.component_name)
                stream_name = message.get("stream", "default")
                num_emitted = self.emitted_counters[component.component_name][
                    stream_name
                ]
                if num_emitted % 20 == 0:
                    print(
                        "Cumulative count of tuples emitted for {}__{}: {}".format(
                            component.component_name, stream_name, num_emitted
                        )
                    )
            elif command == "sync":
                # Ignore outputs from a spout after a sync until FakeStorm sends it a next/ack/fail
                self.ignored_spouts.add(component.component_name)
            elif command == "ack":
                self.ack(message["id"])
            # Send fail to spout and update tuple tree
            elif command == "fail":
                self.fail(message["id"])
            else:
                print("Missed this command: {}".format(message))
            message = component.serializer.read_message(
                stream=component.serializer.output_stream
            )

    def run(self, running_time):
        """Start it up"""
        now = time.time()
        if running_time <= 0:
            running_time = float("inf")
        self.start_time = now
        self.end_time = now + running_time
        last_tick = 0
        while now < self.end_time:
            # Send tick tuples if necessary:
            if now - last_tick > self.tick_freq:
                for bolt_obj in self.bolts.values():
                    tup_id = "{}__tick__{}".format(bolt_obj.component_name, now)
                    command = {
                        "command": "emit",
                        "comp": "__system",
                        "stream": "__tick",
                        "tuple": [now],
                        "task": -1,
                        "id": tup_id,
                    }
                    self.unacked_tuples[tup_id] = TupleMetadata(
                        tup_id, "__system", "__tick", ["__system"], set(), [now]
                    )
                    # Read command and call process
                    self.read_and_process(bolt_obj)
                    bolt_obj.serializer.send_message(
                        command, stream=bolt_obj.serializer.input_stream
                    )
                    self.read_and_process(bolt_obj)

            # Loop through spouts calling next_tuple()
            for spout_obj in self.spouts.values():
                max_pending = spout_obj.storm_conf["topology.max.spout.pending"]
                currently_pending = self.spout_pending[spout_obj.component_name]
                # check if we are over max.spout.pending
                if currently_pending > max_pending:
                    print(
                        "More than {} tuples pending for {}: {}".format(
                            max_pending, spout_obj.component_name, currently_pending
                        )
                    )
                    continue
                # Stop ignoring spout output from previous sync
                self.ignored_spouts.discard(spout_obj.component_name)
                # Create next_tuple command
                spout_obj.serializer.send_message(
                    {"command": "next"}, stream=spout_obj.serializer.input_stream
                )
                # Read command and call process
                self.read_and_process(spout_obj)

            while True:
                for bolt_obj in self.bolts.values():
                    # Read command and call process
                    self.read_and_process(bolt_obj)
                else:
                    break
            now = time.time()
        print("Stopped execution after {} seconds".format(now - self.start_time))


def run_python_topology(
    name=None,
    env_name=None,
    running_time=0,
    options=None,
    config_file=None,
    override_name=None,
):
    """Run a topology locally using only Python."""
    name, topology_file = get_topology_definition(name, config_file=config_file)
    config = get_config(config_file=config_file)
    env_name, env_config = get_env_config(env_name, config_file=config_file)
    topology_class = get_topology_from_file(topology_file)
    if override_name is None:
        override_name = name
    env_config["serializer"] = "fake"
    set_topology_serializer(env_config, config, topology_class)

    storm_options = resolve_options(
        options, env_config, topology_class, override_name, local_only=True
    )
    if storm_options["topology.acker.executors"] != 0:
        storm_options["topology.acker.executors"] = 1
    storm_options["topology.workers"] = 1
    storm_options["topology.name"] = name

    fake_storm = FakeStorm(topology_class, env_name, storm_options)
    fake_storm.run(running_time)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser(
        "run_pure",
        description=__doc__,
        help=main.__doc__,
        formatter_class=RawDescriptionHelpFormatter,
    )
    subparser.set_defaults(func=main)
    add_ackers(subparser)
    add_config(subparser)
    add_debug(subparser)
    add_environment(subparser)
    add_name(subparser)
    add_options(subparser)
    add_override_name(subparser)
    subparser.add_argument(
        "-t",
        "--time",
        default=0,
        type=int,
        help="Time (in seconds) to keep local cluster "
        "running. If time <= 0, run indefinitely. "
        "(default: %(default)s)",
    )
    add_workers(subparser)


def main(args):
    """Run a pure Python topology locally with the given arguments"""
    run_python_topology(
        name=args.name,
        running_time=args.time,
        options=args.options,
        env_name=args.environment,
        config_file=args.config,
    )


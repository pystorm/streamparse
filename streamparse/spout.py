"""
Base Spout classes.
"""

from __future__ import absolute_import, print_function, unicode_literals

from six import PY3

from .base import Component
from .ipc import read_handshake, read_command, send_message, json, _stdout


class Spout(Component):
    """Base class for all streamparse spouts.

    For more information on spouts, consult Storm's
    `Concepts documentation <http://storm.incubator.apache.org/documentation/Concepts.html>`_.
    """

    def initialize(self, storm_conf, context):
        """Called immediately after the initial handshake with Storm and before
        the main run loop. A good place to initialize connections to data
        sources.

        :param storm_conf: the Storm configuration for this Bolt.  This is the
                           configuration provided to the topology, merged in
                           with cluster configuration on the worker node.
        :type storm_conf: dict
        :param context: information about the component's place within the
                        topology such as: task IDs, inputs, outputs etc.
        :type context: dict
        """
        pass

    def ack(self, tup_id):
        """Called when a bolt acknowledges a tuple in the topology.

        :param tup_id: the ID of the tuple that has been fully acknowledged in
                       the topology.
        :type tup_id: str
        """
        pass

    def fail(self, tup_id):
        """Called when a tuple fails in the topology

        A Spout can choose to emit the tuple again or ignore the fail. The
        default is to ignore.

        :param tup_id: the ID of the tuple that has failed in the topology
                       either due to a bolt calling ``fail()`` or a tuple
                       timing out.
        :type tup_id: str
        """
        pass

    def next_tuple(self):
        """Implement this function to emit tuples as necessary.

        This function should not block, or Storm will think the
        spout is dead. Instead, let it return and streamparse will
        send a noop to storm, which lets it know the spout is functioning.
        """
        raise NotImplementedError()

    def emit(self, tup, tup_id=None, stream=None, direct_task=None):
        """Emit a spout tuple message.

        :param tup: the tuple to send to Storm.  Should contain only
                    JSON-serializable data.
        :type tup: list
        :param tup_id: the ID for the tuple. Leave this blank for an
                       unreliable emit.
        :type tup_id: str
        :param stream: ID of the stream this tuple should be emitted to.
                       Leave empty to emit to the default stream.
        :type stream: str
        :param direct_task: the task to send the tuple to if performing a
                            direct emit.
        :type direct_task: int
        """
        if not isinstance(tup, list):
            raise TypeError('All tuples must be lists, received {!r} instead'
                            .format(type(tup)))

        msg = {'command': 'emit', 'tuple': tup}
        if tup_id is not None:
            msg['id'] = tup_id
        if stream is not None:
            msg['stream'] = stream
        if direct_task is not None:
            msg['task'] = direct_task

        send_message(msg)

    def emit_many(self, tuples, tup_id=None, stream=None, direct_task=None):
        """A more efficient way to send many tuples.

        Dumps out all tuples to STDOUT instead of writing one at a time.

        :param tuples: a two-dimensional ``list`` representing the tuples to
                       send to Storm.  Tuples should contain only
                       JSON-serializable data.
        :type tuples: list
        :param tup_id: the id for the tuple.  Leave this blank for unreliable
                       emits.
        :type tup_id: str
        :param stream: ID of the stream these tuples should be emitted to.
                       Leave empty to emit to the default stream.
        :type stream: str
        :param direct_task: the task to send the tuple to if
                            performing a direct emit.
        :type direct_task: int
        """
        msg = {
            'command': 'emit',
        }
        if tup_id is not None:
            msg['id'] = tup_id
        if stream is not None:
            msg['stream'] = stream
        if direct_task is not None:
            msg['task'] = direct_task

        lines = []
        for tup in tuples:
            msg['tuple'] = tup
            lines.append(json.dumps(msg))
        wrapped_msg = "{}\nend\n".format("\nend\n".join(lines)).encode('utf-8')
        if PY3:
            _stdout.flush()
            _stdout.buffer.write(wrapped_msg)
        else:
            _stdout.write(wrapped_msg)
        _stdout.flush()

    def run(self):
        """Main run loop for all spouts.

        Performs initial handshake with Storm and reads tuples handing them off
        to subclasses.  Any exceptions are caught and logged back to Storm
        prior to the Python process exiting.

        Subclasses should **not** override this method.
        """
        storm_conf, context = read_handshake()
        try:
            self.initialize(storm_conf, context)
            while True:
                cmd = read_command()
                if cmd['command'] == 'next':
                    self.next_tuple()
                if cmd['command'] == 'ack':
                    self.ack(cmd['id'])
                if cmd['command'] == 'fail':
                    self.fail(cmd['id'])
                send_message({'command': 'sync'})
        except Exception as e:
            self.raise_exception(e)

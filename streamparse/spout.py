"""Base Spout classes."""
from ipc import read_handshake, read_command, send_message, json, _stdout
from base import Component


class Spout(Component):
    """Base class for all streamparse spouts.  For more information on spouts,
    consult Storm's `Concepts documentation <http://storm.incubator.apache.org/documentation/Concepts.html>`_.
    """

    def initialize(self, storm_conf, context):
        """Called immediately after the initial handshake with Storm and before
        the main run loop. A good place to initialize connections to data
        sources.

        :param storm_conf: a ``dict`` containing the Storm configuration for
        this spout.  This is the configuration provided to the topology, merged
        in with cluster configuration on the worker node.
        :param context: a ``dict`` containing information about the component's
        place within the topology such as: task IDs, inputs, outputs etc."""
        pass

    def ack(self, tup_id):
        """Called when a bolt acknowledges a tuple in the topology.

        :param tup_id: a ``str`` representing the tuple that was acknowledged.
        """
        pass

    def fail(self, tup_id):
        """Called when a tuple fails in the topology, a Spout can choose to
        emit the tuple again or ignore the fail.  Default is to ignore.

        :param tup_id: a ``str`` representing the tuple that was failed.
        """
        pass

    def next_tuple(self):
        raise NotImplementedError()

    def emit(self, tup, tup_id=None, stream=None, direct_task=None):
        """Emit a spout tuple message.

        :param tup: a ``list`` representing the tuple to send to Storm.  Should
        contain only JSON-serializable data.
        :param tup_id: ``str`` or ``int`` which is the id for the tuple. Leave
        this blank for an unreliable emit.
        :param stream: ``str`` ID of the stream this tuple should be emitted
        to.  Leave empty to emit to the default stream.
        :param direct_task: ``int`` indicating the task to send the tuple to if
        performing a direct emit.
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
        """A more efficient way to send many tuples, dumps out all tuples to
        STDOUT instead of writing one at a time.

        :param tuples: a two-dimensional ``list`` representing the tuples to
        send to Storm.  Tuples should contain only JSON-serializable data.
        :param tup_id: ``str`` or ``int`` which is the id for the tuple.  Leave
        this blank for unreliable emits.
        :param stream: ``str`` ID of the stream these tuples should be emitted
        to.  Leave empty to emit to the default stream.
        :param direct_task: ``int`` indicating the task to send the tuple to if
        performing a direct emit.
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
        _stdout.write("{}\nend\n".format("\nend\n".join(lines)))
        _stdout.flush()

    def run(self):
        """Main run loop for all spouts. Performs initial handshake with Storm
        and reads tuples handing them off to subclasses.  Any exceptions are
        caught and logged back to Storm prior to the Python process exits.
        Subclasses should not override this method.
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

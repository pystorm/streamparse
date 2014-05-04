from __future__ import print_function

from .util import read_handshake, read_command, send_message, Component, json
from .util import _stdout


class Spout(Component):

    def initialize(self, storm_conf, context):
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

        :param tup: a ``list`` representing the tuple to send to Storm, should
                    contain only JSON-serializable data.
        :param tup_id: ``str`` or ``int`` which is the id for the tuple. Leave
                    this blank for an unreliable emit.
        :param stream: ``str`` ID of the stream this tuple should be emitted
                    to.  Leave empty to emit to the default stream.
        :param direct_task: ``int`` indicating the task to send the tuple to if
                    performing a direct emit.
        """
        if not isinstance(tup, list):
            raise TypeError('All tuples must be lists, received {!r} instead'\
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
            lines.append('end')
        print('\n'.join(lines), file=_stdout)

    def run(self):
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

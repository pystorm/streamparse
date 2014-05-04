from __future__ import print_function

from .util import read_handshake, read_tuple, send_message, Component, json
from .util import _stdout


_ANCHOR_TUPLE = None

class Bolt(Component):

    def initialize(self, storm_conf, context):
        """Process initialization after Storm configuration and topology
        context are received from the worker process.
        """
        pass

    def process(self, tup):
        """Main method for tuple processing, must be overridden by subclasses.

        :param tup: a ``Tuple`` object.
        """
        raise NotImplementedError()

    def emit(self, tup, stream=None, anchors=[], direct_task=None):
        """Emit a bolt tuple message.

        :param tup: a ``list`` representing the tuple ot send to Storm, should
                    contain only JSON-serializable data.
        :param stream: a ``str`` indicating the ID of the stream to emit this
                       tuple to.  Leave empty to emit to default stream.
        :param anchors: a ``list`` which is the IDs of the tuples this output
                        tuple should be anchored to.
        :param direct_task: an ``int`` which indicates the task to send the
                            tuple to.
        """
        if not isinstance(tup, list):
            raise TypeError('All tuples must be lists, received {!r} instead'\
                            .format(type(tup)))
        if _ANCHOR_TUPLE is not None:
            anchors = [_ANCHOR_TUPLE]
        msg = {'command': 'emit', 'tuple': tup}
        if stream is not None:
            msg['stream'] = stream
        msg['anchors'] = [x.id for x in anchors]
        if direct_task is not None:
            msg['task'] = direct_task

        send_message(msg)

    def emit_many(self, tuples, stream=None, anchors=[], direct_task=None):
        """A more efficient way to send many tuples, dumps out all tuples to
        STDOUT instead of writing one at a time.
        """
        if _ANCHOR_TUPLE is not None:
            anchors = [_ANCHOR_TUPLE]
        msg = {
            'command': 'emit',
            'anchors': [a.id for a in anchors],
        }
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

    def ack(self, tup):
        """Acknowledge a tuple.

        :param tup: a ``Tuple`` object.
        """
        send_message({'command': 'ack', 'id': tup.id})

    def fail(self, tup):
        """Fail a tuple.

        :param tup: a ``Tuple`` object.
        """
        send_message({'command': 'fail', 'id': tup.id})

    def run(self):
        """Main run loop for all bolts, performs initial handshake and
        reads tuples handing them off to the subclass.  Any exceptions are
        caught and sent back to Storm as a proper exception.
        """
        storm_conf, context = read_handshake()
        try:
            self.initialize(storm_conf, context)
            while True:
                tup = read_tuple()
                self.process(tup)
        except Exception as e:
            self.raise_exception(e)


class BasicBolt(Bolt):

    def run(self):
        global _ANCHOR_TUPLE
        storm_conf, context = read_handshake()
        try:
            self.initialize(storm_conf, context)
            while True:
                tup = read_tuple()
                _ANCHOR_TUPLE = tup
                self.process(tup)
                self.ack(tup)
        except Exception as e:
            self.raise_exception(e)


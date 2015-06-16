"""
Base Spout classes.
"""

from __future__ import absolute_import, print_function, unicode_literals

import itertools
import logging

from six.moves import zip

from .component import Component


log = logging.getLogger(__name__)


class Spout(Component):
    """Base class for all streamparse spouts.

    For more information on spouts, consult Storm's
    `Concepts documentation <http://storm.incubator.apache.org/documentation/Concepts.html>`_.
    """

    def initialize(self, storm_conf, context):
        """Called immediately after the initial handshake with Storm and before
        the main run loop. A good place to initialize connections to data
        sources.

        :param storm_conf: the Storm configuration for this Spout.  This is the
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

    def emit(self, tup, tup_id=None, stream=None, direct_task=None,
             need_task_ids=True):
        """Emit a spout tuple message.

        :param tup: the tuple to send to Storm, should contain only
                    JSON-serializable data.
        :type tup: list or tuple
        :param tup_id: the ID for the tuple. Leave this blank for an
                       unreliable emit.
        :type tup_id: str
        :param stream: ID of the stream this tuple should be emitted to.
                       Leave empty to emit to the default stream.
        :type stream: str
        :param direct_task: the task to send the tuple to if performing a
                            direct emit.
        :type direct_task: int
        :param need_task_ids: indicate whether or not you'd like the task IDs
                              the tuple was emitted (default:
                              ``True``).
        :type need_task_ids: bool

        :returns: a ``list`` of task IDs that the tuple was sent to. Note that
                  when specifying direct_task, this will be equal to
                  ``[direct_task]``. If you specify ``need_task_ids=False``,
                  this function will return ``None``.
        """
        return super(Spout, self).emit(tup, tup_id=tup_id, stream=stream,
                                       direct_task=direct_task,
                                       need_task_ids=need_task_ids)

    def emit_many(self, tuples, stream=None, tup_ids=None, direct_task=None,
                  need_task_ids=True):
        """Emit multiple tuples.

        :param tuples: a ``list`` of multiple tuple payloads to send to
                       Storm. All tuples should contain only
                       JSON-serializable data.
        :type tuples: list
        :param stream: the ID of the steram to emit these tuples to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param tup_ids: the ID for the tuple. Leave this blank for an
                       unreliable emit.
        :type tup_ids: list
        :param tup_ids: IDs for each of the tuples in the list.  Omit these for
                        an unreliable emit.
        :type anchors: list
        :param direct_task: indicates the task to send the tuple to.
        :type direct_task: int
        :param need_task_ids: indicate whether or not you'd like the task IDs
                              the tuple was emitted (default:
                              ``True``).
        :type need_task_ids: bool

        .. deprecated:: 2.0.0
            Just call :py:meth:`Spout.emit` repeatedly instead.
        """
        if not isinstance(tuples, (list, tuple)):
            raise TypeError('tuples should be a list of lists/tuples, '
                            'received {!r} instead.'.format(type(tuples)))

        all_task_ids = []
        if tup_ids is None:
            tup_ids = itertools.repeat(None)

        for tup, tup_id in zip(tuples, tup_ids):
            all_task_ids.append(self.emit(tup, stream=stream, tup_id=tup_id,
                                          direct_task=direct_task,
                                          need_task_ids=need_task_ids))

        return all_task_ids

    def _run(self):
        """The inside of ``run``'s infinite loop.

        Separated out so it can be properly unit tested.
        """
        cmd = self.read_command()
        if cmd['command'] == 'next':
            self.next_tuple()
        elif cmd['command'] == 'ack':
            self.ack(cmd['id'])
        elif cmd['command'] == 'fail':
            self.fail(cmd['id'])
        else:
            self.logger.error('Received invalid command from Storm: %r', cmd)
        self.send_message({'command': 'sync'})

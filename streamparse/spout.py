"""
Base Spout classes.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging

from six import PY3

from .base import Component
from .ipc import (read_handshake, read_command, read_task_ids, send_message,
                  json)


log = logging.getLogger('streamparse.spout')


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

    def emit(self, tup, tup_id=None, stream=None, direct_task=None,
             need_task_ids=None):
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
        :param need_task_ids: indicate whether or not you'd like the task IDs
                              the tuple was emitted (default:
                              ``True``).
        :type need_task_ids: bool

        :returns: a ``list`` of task IDs that the tuple was sent to. Note that
                  when specifying direct_task, this will be equal to
                  ``[direct_task]``. If you specify ``need_task_ids=False``,
                  this function will return ``None``.
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

        if need_task_ids is None:
            need_task_ids = True
        elif need_task_ids is False:
            # only need to send on False, Storm's default is True
            msg['need_task_ids'] = need_task_ids

        send_message(msg)

        if need_task_ids == True:
            downstream_task_ids = [direct_task] if direct_task is not None \
                                  else read_task_ids()
            return downstream_task_ids
        else:
            return None

    def emit_many(self, tuples, stream=None, anchors=None, direct_task=None,
                  need_task_ids=None):
        """Emit multiple tuples.

        :param tuples: a ``list`` containing ``list`` s of tuple payload data
                       to send to Storm. All tuples should contain only
                       JSON-serializable data.
        :type tuples: list
        :param stream: the ID of the steram to emit these tuples to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param anchors: IDs the tuples (or :class:`streamparse.ipc.Tuple`
                        instances) which the emitted tuples should be anchored
                        to. If ``auto_anchor`` is set to ``True`` and
                        you have not specified ``anchors``, ``anchors`` will be
                        set to the incoming/most recent tuple ID(s).
        :type anchors: list
        :param direct_task: indicates the task to send the tuple to.
        :type direct_task: int
        :param need_task_ids: indicate whether or not you'd like the task IDs
                              the tuple was emitted (default:
                              ``True``).
        :type need_task_ids: bool
        """
        if not isinstance(tuples, list):
            raise TypeError('tuples should be a list of lists, received {!r}'
                            'instead.'.format(type(tuples)))

        all_task_ids = []
        for tup in tuples:
            all_task_ids.append(self.emit(tup, stream=stream, anchors=anchors,
                                          direct_task=direct_task,
                                          need_task_ids=need_task_ids))

        return all_task_ids

    def run(self):
        """Main run loop for all spouts.

        Performs initial handshake with Storm and reads tuples handing them off
        to subclasses.  Any exceptions are caught and logged back to Storm
        prior to the Python process exiting.

        Subclasses should **not** override this method.
        """
        storm_conf, context = read_handshake()
        self._setup_component(storm_conf, context)

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
            log.error('Error in %s.run()', self.__class__.__name__,
                      exc_info=True)
            self.raise_exception(e)

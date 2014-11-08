"""Base Bolt classes."""
from __future__ import absolute_import, print_function, unicode_literals

from collections import defaultdict
import os
import signal
import sys
import threading
import time
import warnings
import logging

from six import iteritems, reraise, PY3

from .base import Component
from .ipc import (read_handshake, read_tuple, read_task_ids, send_message,
                  json, Tuple)


log = logging.getLogger('streamparse.bolt')


class Bolt(Component):
    """The base class for all streamparse bolts.

    For more information on bolts, consult Storm's
    `Concepts documentation <http://storm.incubator.apache.org/documentation/Concepts.html>`_.

    **Example**:

    .. code-block:: python

        from streamparse.bolt import Bolt

        class SentenceSplitterBolt(Bolt):

            def process(self, tup):
                sentence = tup.values[0]
                for word in sentence.split(" "):
                    self.emit([word])
    """

    auto_anchor = True
    """A ``bool`` indicating whether or not the bolt should automatically
    anchor emits to the incoming tuple ID. Tuple anchoring is how Storm
    provides reliability, you can read more about `tuple anchoring in Storm's
    docs <https://storm.incubator.apache.org/documentation/Guaranteeing-message-processing.html#what-is-storms-reliability-api>`_.
    Default is ``True``.
    """
    auto_ack = True
    """A ``bool`` indicating whether or not the bolt should automatically
    acknowledge tuples after ``process()`` is called. Default is ``True``.
    """
    auto_fail = True
    """A ``bool`` indicating whether or not the bolt should automatically fail
    tuples when an exception occurs when the ``process()`` method is called.
    Default is ``True``.
    """

    # Using a list so Bolt and subclasses can have more than one current_tup
    _current_tups = []

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

    def process(self, tup):
        """Process a single tuple :class:`streamparse.ipc.Tuple` of input

        This should be overridden by subclasses.
        :class:`streamparse.ipc.Tuple` objects contain metadata about which
        component, stream and task it came from. The actual values of the
        tuple can be accessed by calling ``tup.values``.

        :param tup: the tuple to be processed.
        :type tup: streamparse.ipc.Tuple
        """
        raise NotImplementedError()

    def emit(self, tup, stream=None, anchors=None, direct_task=None,
             need_task_ids=None):
        """Emit a new tuple to a stream.

        :param tup: the Tuple payload to send to Storm, should contain only
                    JSON-serializable data.
        :type tup: list
        :param stream: the ID of the stream to emit this tuple to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param anchors: IDs the tuples (or :class:`streamparse.ipc.Tuple`
                        instances) which the emitted tuples should be anchored
                        to. If ``auto_anchor`` is set to ``True`` and
                        you have not specified ``anchors``, ``anchors`` will be
                        set to the incoming/most recent tuple ID(s).
        :type anchors: list
        :param direct_task: the task to send the tuple to.
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
            raise TypeError('All tuples must be lists, received {!r} instead.'
                            .format(type(tup)))

        msg = {'command': 'emit', 'tuple': tup}

        if anchors is None:
            anchors = self._current_tups if self.auto_anchor else []
        msg['anchors'] = [a.id if isinstance(a, Tuple) else a for a in anchors]

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

    def ack(self, tup):
        """Indicate that processing of a tuple has succeeded.

        :param tup: the tuple to acknowledge.
        :type tup: str or Tuple
        """
        tup_id = tup.id if isinstance(tup, Tuple) else tup
        send_message({'command': 'ack', 'id': tup_id})

    def fail(self, tup):
        """Indicate that processing of a tuple has failed.

        :param tup: the tuple to fail (``id`` if ``str``).
        :type tup: str or Tuple
        """
        tup_id = tup.id if isinstance(tup, Tuple) else tup
        send_message({'command': 'fail', 'id': tup_id})

    def run(self):
        """Main run loop for all bolts.

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
                self._current_tups = [read_tuple()]
                self.process(self._current_tups[0])
                if self.auto_ack:
                    self.ack(self._current_tups[0])
                # reset so that we don't accidentally fail the wrong tuples
                # if a successive call to read_tuple fails
                self._current_tups = []
        except Exception as e:
            log_msg = "Exception in {}.run()".format(self.__class__.__name__)

            if len(self._current_tups) == 1:
                tup = self._current_tups[0]
                log_msg = "{} while processing {!r}".format(log_msg, tup)
                self.raise_exception(e, tup)
                if self.auto_fail:
                    self.fail(tup)

            log.error(log_msg, exc_info=True)
            sys.exit(1)


class BatchingBolt(Bolt):
    """A bolt which batches tuples for processing.

    Batching tuples is unexpectedly complex to do correctly. The main problem
    is that all bolts are single-threaded. The difficult comes when the
    topology is shutting down because Storm stops feeding the bolt tuples. If
    the bolt is blocked waiting on stdin, then it can't process any waiting
    tuples, or even ack ones that were asynchronously written to a data store.

    This bolt helps with that grouping tuples based on a time interval and then
    processing them on a worker thread.

    To use this class, you must implement ``process_batch``. ``group_key`` can
    be optionally implemented so that tuples are grouped before
    ``process_batch`` is even called.

    **Example**:

    .. code-block:: python

        from streamparse.bolt import BatchingBolt

        class WordCounterBolt(BatchingBolt):

            secs_between_batches = 5

            def group_key(self, tup):
                word = tup.values[0]
                return word  # collect batches of words

            def process_batch(self, key, tups):
                # emit the count of words we had per 5s batch
                self.emit([key, len(tups)])

    """

    auto_anchor = True
    """A ``bool`` indicating whether or not the bolt should automatically
    anchor emits to the incoming tuple ID. Tuple anchoring is how Storm
    provides reliability, you can read more about `tuple anchoring in Storm's
    docs <https://storm.incubator.apache.org/documentation/Guaranteeing-message-processing.html#what-is-storms-reliability-api>`_.
    Default is ``True``.
    """
    auto_ack = True
    """A ``bool`` indicating whether or not the bolt should automatically
    acknowledge tuples after ``process_batch()`` is called. Default is
    ``True``.
    """
    auto_fail = True
    """A ``bool`` indicating whether or not the bolt should automatically fail
    tuples when an exception occurs when the ``process_batch()`` method is
    called. Default is ``True``.
    """
    secs_between_batches = 2
    """The time (in seconds) between calls to ``process_batch()``. Note that if
    there are no tuples in any batch, the BatchingBolt will continue to sleep.
    Note: Can be fractional to specify greater precision (e.g. 2.5).
    """

    def __init__(self):
        super(BatchingBolt, self).__init__()
        self.exc_info = None
        signal.signal(signal.SIGINT, self._handle_worker_exception)

        iname = self.__class__.__name__
        threading.current_thread().name = '{}:main-thread'.format(iname)
        self._batches = defaultdict(list)
        self._batch_lock = threading.Lock()
        self._batcher = threading.Thread(target=self._batch_entry)
        self._batcher.name = '{}:_batcher-thread'.format(iname)
        self._batcher.daemon = True
        self._batcher.start()

    def group_key(self, tup):
        """Return the group key used to group tuples within a batch.

        By default, returns None, which put all tuples in a single
        batch, effectively just time-based batching. Override this create
        multiple batches based on a key.

        :param tup: the tuple used to extract a group key
        :type tup: Tuple
        :returns: Any ``hashable`` value.
        """
        return None

    def process_batch(self, key, tups):
        """Process a batch of tuples. Should be overridden by subclasses.

        :param key: the group key for the list of batches.
        :type key: hashable
        :param tups: a `list` of :class:`streamparse.ipc.Tuple` s for the group.
        :type tups: list
        """
        raise NotImplementedError()

    def emit(self, tup, **kwargs):
        """Modified emit that will not return task IDs after emitting.

        See :class:`streamparse.ipc.Bolt` for more information.

        :returns: ``None``.
        """
        kwargs['need_task_ids'] = False
        return super(BatchingBolt, self).emit(tup, **kwargs)

    def emit_many(self, tups, **kwargs):
        """Modified emit_many that will not return task IDs after emitting.

        See :class:`streamparse.ipc.Bolt` for more information.

        :returns: ``None``.
        """
        kwargs['need_task_ids'] = False
        return super(BatchingBolt, self).emit_many(tups, **kwargs)

    def run(self):
        """Modified and simplified run loop which runs in the main thread since
        we only need to add tuples to the proper batch for later processing
        in the _batcher thread.
        """
        storm_conf, context = read_handshake()
        self._setup_component(storm_conf, context)

        tup = None
        try:
            self.initialize(storm_conf, context)
            while True:
                tup = read_tuple()
                group_key = self.group_key(tup)
                with self._batch_lock:
                    self._batches[group_key].append(tup)
        except Exception as e:
            log.error("Exception in %s.run() while adding %r to batch",
                      self.__class__.__name__, tup, exc_info=True)
            self.raise_exception(e)

    def _batch_entry(self):
        """Entry point for the batcher thread."""
        try:
            while True:
                time.sleep(self.secs_between_batches)
                with self._batch_lock:
                    if not self._batches:
                        # No tuples to save
                        continue

                    for key, batch in iteritems(self._batches):
                        self._current_tups = batch
                        self.process_batch(key, batch)
                        if self.auto_ack:
                            for tup in batch:
                                self.ack(tup)

                    self._batches = defaultdict(list)

        except Exception as e:
            log_msg = ("Exception in {}.run() while processing tuple batch "
                       "{!r}.".format(self.__class__.__name__,
                                      self._current_tups))
            log.error(log_msg, exc_info=True)
            self.raise_exception(e, self._current_tups)

            if self.auto_fail and self._current_tups:
                for tup in self._current_tups:
                    self.fail(tup)

            self.exc_info = sys.exc_info()
            os.kill(os.getpid(), signal.SIGINT)  # interrupt stdin waiting

    def _handle_worker_exception(self, signum, frame):
        """Handle an exception raised in the worker thread.

        Exceptions in the _batcher thread will send a SIGINT to the main
        thread which we catch here, and then raise in the main thread.
        """
        reraise(*self.exc_info)


class BasicBolt(Bolt):

    def __init__(self):
        super(BasicBolt, self).__init__()
        warnings.warn("BasicBolt is deprecated and "
                      "will be removed in a future streamparse release. "
                      "Please use Bolt.", DeprecationWarning)

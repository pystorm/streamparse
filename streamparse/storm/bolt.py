"""Base Bolt classes."""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
import signal
import sys
import threading
import time
from collections import defaultdict

from six import iteritems, itervalues, string_types, reraise
from six.moves import range

from .component import Component, Tuple


log = logging.getLogger(__name__)


class Bolt(Component):
    """The base class for all streamparse bolts.

    For more information on bolts, consult Storm's
    `Concepts documentation <http://storm.incubator.apache.org/documentation/Concepts.html>`_.

    :ivar auto_anchor: A ``bool`` indicating whether or not the bolt should
                       automatically anchor emits to the incoming tuple ID.
                       Tuple anchoring is how Storm provides reliability, you
                       can read more about
                       `tuple anchoring in Storm's docs <https://storm.incubator.apache.org/documentation/Guaranteeing-message-processing.html#what-is-storms-reliability-api>`_.
                       Default is ``True``.

    :ivar auto_ack: A ``bool`` indicating whether or not the bolt should
                    automatically acknowledge tuples after ``process()``
                    is called. Default is ``True``.
    :ivar auto_fail: A ``bool`` indicating whether or not the bolt should
                     automatically fail tuples when an exception occurs when the
                     ``process()`` method is called. Default is ``True``.

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
    auto_ack = True
    auto_fail = True

    # Using a list so Bolt and subclasses can have more than one current_tup
    _current_tups = []

    @classmethod
    def spec(cls, **kwargs):
        return BoltSpecification(cls, **kwargs)

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
        """Process a single tuple :class:`streamparse.storm.component.Tuple` of
        input

        This should be overridden by subclasses.
        :class:`streamparse.storm.component.Tuple` objects contain metadata
        about which component, stream and task it came from. The actual values
        of the tuple can be accessed by calling ``tup.values``.

        :param tup: the tuple to be processed.
        :type tup: :class:`streamparse.storm.component.Tuple`
        """
        raise NotImplementedError()

    def process_tick(self, freq):
        """Process special 'tick tuples' which allow time-based
        behaviour to be included in bolts.

        Default behaviour is to ignore time ticks.  This should be
        overridden by subclasses who wish to react to timer events
        via tick tuples.

        Tick tuples will be sent to all bolts in a toplogy when the
        storm configuration option 'topology.tick.tuple.freq.secs'
        is set to an integer value, the number of seconds.

        :param freq: the tick frequency, in seconds, as set in the
                     storm configuration `topology.tick.tuple.freq.secs`
        :type freq: int
        """
        pass

    def emit(self, tup, stream=None, anchors=None, direct_task=None,
             need_task_ids=True):
        """Emit a new tuple to a stream.

        :param tup: the Tuple payload to send to Storm, should contain only
                    JSON-serializable data.
        :type tup: :class:`list` or :class:`streamparse.storm.component.Tuple`
        :param stream: the ID of the stream to emit this tuple to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param anchors: IDs the tuples (or :class:`streamparse.storm.component.Tuple`
                        instances) which the emitted tuples should be anchored
                        to. If ``auto_anchor`` is set to ``True`` and
                        you have not specified ``anchors``, ``anchors`` will be
                        set to the incoming/most recent tuple ID(s).
        :type anchors: list
        :param direct_task: the task to send the tuple to.
        :type direct_task: int
        :param need_task_ids: indicate whether or not you'd like the task IDs
                              the tuple was emitted (default: ``True``).
        :type need_task_ids: bool

        :returns: a ``list`` of task IDs that the tuple was sent to. Note that
                  when specifying direct_task, this will be equal to
                  ``[direct_task]``. If you specify ``need_task_ids=False``,
                  this function will return ``None``.
        """
        if not isinstance(tup, (list, tuple)):
            raise TypeError('All tuples must be either lists or tuples, '
                            'received {!r} instead.'.format(type(tup)))

        msg = {'command': 'emit', 'tuple': tup}

        if anchors is None:
            anchors = self._current_tups if self.auto_anchor else []
        msg['anchors'] = [a.id if isinstance(a, Tuple) else a for a in anchors]

        if stream is not None:
            msg['stream'] = stream
        if direct_task is not None:
            msg['task'] = direct_task

        if need_task_ids is False:
            # only need to send on False, Storm's default is True
            msg['need_task_ids'] = need_task_ids

        # Use both locks so we ensure send_message and read_task_ids are for
        # same emit
        with self._reader_lock, self._writer_lock:
            # Message encoding will convert both list and tuple to a JSON array.
            self.send_message(msg)

            if need_task_ids is True:
                downstream_task_ids = [direct_task] if direct_task is not None \
                                      else self.read_task_ids()
                return downstream_task_ids
            else:
                return None

    def emit_many(self, tuples, stream=None, anchors=None, direct_task=None,
                  need_task_ids=None):
        """Emit multiple tuples.

        :param tuples: a ``list`` of multiple tuple payloads to send to
                       Storm. All tuples should contain only
                       JSON-serializable data.
        :type tuples: list
        :param stream: the ID of the steram to emit these tuples to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param anchors: IDs the tuples (or :class:`streamparse.storm.component.Tuple`
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
        if not isinstance(tuples, (list, tuple)):
            raise TypeError('tuples should be a list of lists/tuples, '
                            'received {!r} instead.'.format(type(tuples)))

        all_task_ids = []
        for tup in tuples:
            all_task_ids.append(self.emit(tup, stream=stream, anchors=anchors,
                                          direct_task=direct_task,
                                          need_task_ids=need_task_ids))

        return all_task_ids

    def ack(self, tup):
        """Indicate that processing of a tuple has succeeded.

        :param tup: the tuple to acknowledge.
        :type tup: :class:`str` or :class:`streamparse.storm.component.Tuple`
        """
        tup_id = tup.id if isinstance(tup, Tuple) else tup
        self.send_message({'command': 'ack', 'id': tup_id})

    def fail(self, tup):
        """Indicate that processing of a tuple has failed.

        :param tup: the tuple to fail (its ``id`` if ``str``).
        :type tup: :class:`str` or :class:`streamparse.storm.component.Tuple`
        """
        tup_id = tup.id if isinstance(tup, Tuple) else tup
        self.send_message({'command': 'fail', 'id': tup_id})

    def _run(self):
        """The inside of ``run``'s infinite loop.

        Separated out so it can be properly unit tested.
        """
        self._current_tups = [self.read_tuple()]
        tup = self._current_tups[0]
        if tup.task == -1 and tup.stream == '__heartbeat':
            self.send_message({'command': 'sync'})
        elif tup.component == '__system' and tup.stream == '__tick':
            frequency = tup.values[0]
            self.process_tick(frequency)
        else:
            self.process(tup)
            if self.auto_ack:
                 self.ack(tup)
            # reset so that we don't accidentally fail the wrong tuples
            # if a successive call to read_tuple fails
        self._current_tups = []

    def run(self):
        """Main run loop for all bolts.

        Performs initial handshake with Storm and reads tuples handing them off
        to subclasses.  Any exceptions are caught and logged back to Storm
        prior to the Python process exiting.

        Subclasses should **not** override this method.
        """
        storm_conf, context = self.read_handshake()
        self._setup_component(storm_conf, context)

        try:
            self.initialize(storm_conf, context)
            while True:
                self._run()
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


    :ivar auto_anchor: A ``bool`` indicating whether or not the bolt should
                       automatically anchor emits to the incoming tuple ID.
                       Tuple anchoring is how Storm provides reliability, you
                       can read more about `tuple anchoring in Storm's
                       docs <https://storm.incubator.apache.org/documentation/Guaranteeing-message-processing.html#what-is-storms-reliability-api>`_.
                       Default is ``True``.
    :ivar auto_ack: A ``bool`` indicating whether or not the bolt should
                    automatically acknowledge tuples after ``process_batch()``
                    is called. Default is ``True``.
    :ivar auto_fail: A ``bool`` indicating whether or not the bolt should
                     automatically fail tuples when an exception occurs when the
                     ``process_batch()`` method is called. Default is ``True``.
    :ivar secs_between_batches: The time (in seconds) between calls to
                                ``process_batch()``. Note that if there are no
                                tuples in any batch, the BatchingBolt will
                                continue to sleep.

                                .. note::
                                  Can be fractional to specify greater
                                  precision (e.g. 2.5).

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
    auto_ack = True
    auto_fail = True
    secs_between_batches = 2

    def __init__(self, *args, **kwargs):
        super(BatchingBolt, self).__init__(*args, **kwargs)
        self.exc_info = None
        signal.signal(signal.SIGUSR1, self._handle_worker_exception)

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
        batch, effectively just time-based batching. Override this to create
        multiple batches based on a key.

        :param tup: the tuple used to extract a group key
        :type tup: :class:`streamparse.storm.component.Tuple`
        :returns: Any ``hashable`` value.
        """
        return None

    def process_batch(self, key, tups):
        """Process a batch of tuples. Should be overridden by subclasses.

        :param key: the group key for the list of batches.
        :type key: hashable
        :param tups: a `list` of :class:`streamparse.storm.component.Tuple` s for the group.
        :type tups: list
        """
        raise NotImplementedError()

    def emit(self, tup, **kwargs):
        """Modified emit that will not return task IDs after emitting.

        See :class:`streamparse.storm.component.Bolt` for more information.

        :returns: ``None``.
        """
        kwargs['need_task_ids'] = False
        return super(BatchingBolt, self).emit(tup, **kwargs)

    def emit_many(self, tups, **kwargs):
        """Modified emit_many that will not return task IDs after emitting.

        See :class:`streamparse.storm.component.Bolt` for more information.

        :returns: ``None``.
        """
        kwargs['need_task_ids'] = False
        return super(BatchingBolt, self).emit_many(tups, **kwargs)

    def _run(self):
        """The inside of ``run``'s infinite loop.

        Separated out so it can be properly unit tested.
        """
        tup = None
        try:
            tup = self.read_tuple()
            if tup.task == -1 and tup.stream == '__heartbeat':
                self.send_message({'command': 'sync'})
            elif tup.component == '__system' and tup.stream == '__tick':
                frequency = tup.values[0]
                self.process_tick(frequency)
            else:
                group_key = self.group_key(tup)
                with self._batch_lock:
                    self._batches[group_key].append(tup)
        except Exception as e:
            log.error("Exception in %s.run() while adding %r to batch",
                      self.__class__.__name__, tup, exc_info=True)
            self.raise_exception(e)

    def run(self):
        """Modified and simplified run loop which runs in the main thread since
        we only need to add tuples to the proper batch for later processing
        in the _batcher thread.
        """
        storm_conf, context = self.read_handshake()
        self._setup_component(storm_conf, context)

        tup = None
        self.initialize(storm_conf, context)
        while True:
            self._run()

    def _batch_entry_run(self):
        """The inside of ``_batch_entry``'s infinite loop.

        Separated out so it can be properly unit tested.
        """
        time.sleep(self.secs_between_batches)
        with self._batch_lock:
            if not self._batches:
                return # no tuples to save
            for key, batch in iteritems(self._batches):
                self._current_tups = batch
                self.process_batch(key, batch)
                if self.auto_ack:
                    for tup in batch:
                        self.ack(tup)
                # Set current batch to [] so that we know it was acked if a
                # later batch raises an exception
                self._batches[key] = []
            self._batches = defaultdict(list)

    def _batch_entry(self):
        """Entry point for the batcher thread."""
        try:
            while True:
                self._batch_entry_run()
        except Exception as e:
            log_msg = ("Exception in {}.run() while processing tuple batch "
                       "{!r}.".format(self.__class__.__name__,
                                      self._current_tups))
            log.error(log_msg, exc_info=True)
            self.raise_exception(e, self._current_tups)

            if self.auto_fail:
                with self._batch_lock:
                    for batch in itervalues(self._batches):
                        for tup in batch:
                            self.fail(tup)

            self.exc_info = sys.exc_info()
            os.kill(self.pid, signal.SIGUSR1)  # interrupt stdin waiting

    def _handle_worker_exception(self, signum, frame):
        """Handle an exception raised in the worker thread.

        Exceptions in the _batcher thread will send a SIGUSR1 to the main
        thread which we catch here, and then raise in the main thread.
        """
        reraise(*self.exc_info)

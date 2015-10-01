"""Base bolt classes."""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
import signal
import sys
import threading
import time
from collections import defaultdict

from six import iteritems, itervalues

from .component import Component, Tuple


log = logging.getLogger(__name__)


class Bolt(Component):
    """The base class for all streamparse bolts.

    For more information on bolts, consult Storm's
    `Concepts documentation <http://storm.apache.org/documentation/Concepts.html>`_.

    :ivar auto_anchor: A ``bool`` indicating whether or not the bolt should
                       automatically anchor emits to the incoming Tuple ID.
                       Tuple anchoring is how Storm provides reliability, you
                       can read more about
                       `Tuple anchoring in Storm's docs <https://storm.apache.org/documentation/Guaranteeing-message-processing.html#what-is-storms-reliability-api>`_.
                       Default is ``True``.

    :ivar auto_ack: A ``bool`` indicating whether or not the bolt should
                    automatically acknowledge Tuples after ``process()``
                    is called. Default is ``True``.
    :ivar auto_fail: A ``bool`` indicating whether or not the bolt should
                     automatically fail Tuples when an exception occurs when the
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

    # Using list; Bolt class and subclasses can have more than one current_tup.
    _current_tups = []

    @staticmethod
    def is_tick(tup):
        """ :returns: Whether or not the given Tuple is a tick Tuple """
        return tup.component == '__system' and tup.stream == '__tick'

    def initialize(self, storm_conf, context):
        """Called immediately after the initial handshake with Storm and before
        the main run loop. A good place to initialize connections to data
        sources.

        :param storm_conf: the Storm configuration for this bolt.  This is the
                           configuration provided to the topology, merged in
                           with cluster configuration on the worker node.
        :type storm_conf: dict
        :param context: information about the component's place within the
                        topology such as: task IDs, inputs, outputs etc.
        :type context: dict
        """
        pass

    def process(self, tup):
        """Process a single Tuple :class:`streamparse.storm.component.Tuple` of
        input

        This should be overridden by subclasses.
        :class:`streamparse.storm.component.Tuple` objects contain metadata
        about which component, stream and task it came from. The actual values
        of the Tuple can be accessed by calling ``tup.values``.

        :param tup: the Tuple to be processed.
        :type tup: :class:`streamparse.storm.component.Tuple`
        """
        raise NotImplementedError()

    def process_tick(self, tup):
        """Process special 'tick Tuples' which allow time-based
        behaviour to be included in bolts.

        Default behaviour is to ignore time ticks.  This should be
        overridden by subclasses who wish to react to timer events
        via tick Tuples.

        Tick Tuples will be sent to all bolts in a toplogy when the
        storm configuration option 'topology.tick.tuple.freq.secs'
        is set to an integer value, the number of seconds.

        :param tup: the Tuple to be processed.
        :type tup: :class:`streamparse.storm.component.Tuple`
        """
        pass

    def emit(self, tup, stream=None, anchors=None, direct_task=None,
             need_task_ids=True):
        """Emit a new Tuple to a stream.

        :param tup: the Tuple payload to send to Storm, should contain only
                    JSON-serializable data.
        :type tup: :class:`list` or :class:`streamparse.storm.component.Tuple`
        :param stream: the ID of the stream to emit this Tuple to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param anchors: IDs the Tuples (or :class:`streamparse.storm.component.Tuple`
                        instances) which the emitted Tuples should be anchored
                        to. If ``auto_anchor`` is set to ``True`` and
                        you have not specified ``anchors``, ``anchors`` will be
                        set to the incoming/most recent Tuple ID(s).
        :type anchors: list
        :param direct_task: the task to send the Tuple to.
        :type direct_task: int
        :param need_task_ids: indicate whether or not you'd like the task IDs
                              the Tuple was emitted (default: ``True``).
        :type need_task_ids: bool

        :returns: a ``list`` of task IDs that the Tuple was sent to. Note that
                  when specifying direct_task, this will be equal to
                  ``[direct_task]``. If you specify ``need_task_ids=False``,
                  this function will return ``None``.
        """
        if anchors is None:
            anchors = self._current_tups if self.auto_anchor else []
        anchors = [a.id if isinstance(a, Tuple) else a for a in anchors]

        return super(Bolt, self).emit(tup, stream=stream, anchors=anchors,
                                      direct_task=direct_task,
                                      need_task_ids=need_task_ids)

    def emit_many(self, tuples, stream=None, anchors=None, direct_task=None,
                  need_task_ids=True):
        """Emit multiple Tuples.

        :param tuples: a ``list`` of multiple Tuple payloads to send to
                       Storm. All Tuples should contain only
                       JSON-serializable data.
        :type tuples: list
        :param stream: the ID of the steram to emit these Tuples to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param anchors: IDs the Tuples (or :class:`streamparse.storm.component.Tuple`
                        instances) which the emitted Tuples should be anchored
                        to. If ``auto_anchor`` is set to ``True`` and
                        you have not specified ``anchors``, ``anchors`` will be
                        set to the incoming/most recent Tuple ID(s).
        :type anchors: list
        :param direct_task: indicates the task to send the Tuple to.
        :type direct_task: int
        :param need_task_ids: indicate whether or not you'd like the task IDs
                              the Tuple was emitted (default:
                              ``True``).
        :type need_task_ids: bool

        .. deprecated:: 2.0.0
            Just call :py:meth:`Bolt.emit` repeatedly instead.
        """
        if not isinstance(tuples, (list, tuple)):
            raise TypeError('Tuples should be a list of lists/tuples, '
                            'received {!r} instead.'.format(type(tuples)))

        all_task_ids = []
        for tup in tuples:
            all_task_ids.append(self.emit(tup, stream=stream, anchors=anchors,
                                          direct_task=direct_task,
                                          need_task_ids=need_task_ids))

        return all_task_ids

    def ack(self, tup):
        """Indicate that processing of a Tuple has succeeded.

        :param tup: the Tuple to acknowledge.
        :type tup: :class:`str` or :class:`streamparse.storm.component.Tuple`
        """
        tup_id = tup.id if isinstance(tup, Tuple) else tup
        self.send_message({'command': 'ack', 'id': tup_id})

    def fail(self, tup):
        """Indicate that processing of a Tuple has failed.

        :param tup: the Tuple to fail (its ``id`` if ``str``).
        :type tup: :class:`str` or :class:`streamparse.storm.component.Tuple`
        """
        tup_id = tup.id if isinstance(tup, Tuple) else tup
        self.send_message({'command': 'fail', 'id': tup_id})

    def _run(self):
        """The inside of ``run``'s infinite loop.

        Separated out so it can be properly unit tested.
        """
        self._current_tups = [self.read_tuple()]
        try:
            tup = self._current_tups[0]
            if self.is_heartbeat(tup):
                self.send_message({'command': 'sync'})
            elif self.is_tick(tup):
                self.process_tick(tup)
                if self.auto_ack:
                     self.ack(tup)
            else:
                self.process(tup)
                if self.auto_ack:
                     self.ack(tup)
        finally:
            # reset so that we don't accidentally fail the wrong Tuples
            # if a successive call to read_tuple fails
            self._current_tups = []

    def _handle_run_exception(self, exc):
        """Process an exception encountered while running the ``run()`` loop.

        Called right before program exits.
        """
        super(Bolt, self)._handle_run_exception(exc)

        if len(self._current_tups) == 1:
            tup = self._current_tups[0]
            self.raise_exception(exc, tup)
            if self.auto_fail:
                self.fail(tup)


class BatchingBolt(Bolt):
    """A bolt which batches Tuples for processing.

    Batching Tuples is unexpectedly complex to do correctly. The main problem
    is that all bolts are single-threaded. The difficult comes when the
    topology is shutting down because Storm stops feeding the bolt Tuples. If
    the bolt is blocked waiting on stdin, then it can't process any waiting
    Tuples, or even ack ones that were asynchronously written to a data store.

    This bolt helps with that by grouping Tuples received between tick Tuples
    into batches.

    To use this class, you must implement ``process_batch``. ``group_key`` can
    be optionally implemented so that Tuples are grouped before
    ``process_batch`` is even called.

    You must also set the `topology.tick.tuple.freq.secs` to how frequently you
    would like ticks to be sent.  If you want ``ticks_between_batches`` to work
    the same way ``secs_between_batches`` worked in older versions of
    streamparse, just set `topology.tick.tuple.freq.secs` to 1.  This setting
    can be specified either at the topology level, or in the topology Clojure
    file by adding `:conf {"topology.tick.tuple.freq.secs", 1}` to your
    `python-bolt-spec`.


    :ivar auto_anchor: A ``bool`` indicating whether or not the bolt should
                       automatically anchor emits to the incoming Tuple ID.
                       Tuple anchoring is how Storm provides reliability, you
                       can read more about `Tuple anchoring in Storm's
                       docs <https://storm.apache.org/documentation/Guaranteeing-message-processing.html#what-is-storms-reliability-api>`_.
                       Default is ``True``.
    :ivar auto_ack: A ``bool`` indicating whether or not the bolt should
                    automatically acknowledge Tuples after ``process_batch()``
                    is called. Default is ``True``.
    :ivar auto_fail: A ``bool`` indicating whether or not the bolt should
                     automatically fail Tuples when an exception occurs when the
                     ``process_batch()`` method is called. Default is ``True``.
    :ivar ticks_between_batches: The number of tick Tuples to wait before
                                 processing a batch.


    **Example**:

    .. code-block:: python

        from streamparse.bolt import BatchingBolt

        class WordCounterBolt(BatchingBolt):

            ticks_between_batches = 5

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
    ticks_between_batches = 1

    def __init__(self, *args, **kwargs):
        super(BatchingBolt, self).__init__(*args, **kwargs)
        self._batches = defaultdict(list)
        self._tick_counter = 0

    def group_key(self, tup):
        """Return the group key used to group Tuples within a batch.

        By default, returns None, which put all Tuples in a single
        batch, effectively just time-based batching. Override this to create
        multiple batches based on a key.

        :param tup: the Tuple used to extract a group key
        :type tup: :class:`streamparse.storm.component.Tuple`
        :returns: Any ``hashable`` value.
        """
        return None

    def process_batch(self, key, tups):
        """Process a batch of Tuples. Should be overridden by subclasses.

        :param key: the group key for the list of batches.
        :type key: hashable
        :param tups: a `list` of :class:`streamparse.storm.component.Tuple` s
                     for the group.
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

        .. deprecated:: 2.0.0
            Just call :py:meth:`BatchingBolt.emit` repeatedly instead.

        """
        kwargs['need_task_ids'] = False
        return super(BatchingBolt, self).emit_many(tups, **kwargs)

    def process_tick(self, tick_tup):
        """Increment tick counter, and call ``process_batch`` for all current
        batches if tick counter exceeds ``ticks_between_batches``.

        See :class:`streamparse.storm.component.Bolt` for more information.

        .. warning::
            This method should **not** be overriden.  If you want to tweak
            how Tuples are grouped into batches, override ``group_key``.
        """
        self._tick_counter += 1
        # ACK tick Tuple immediately, since it's just responsible for counter
        self.ack(tick_tup)
        if self._tick_counter > self.ticks_between_batches and self._batches:
            self.process_batches()
            self._tick_counter = 0

    def process_batches(self):
        """Iterate through all batches, call process_batch on them, and ack.

        Separated out for the rare instances when we want to subclass
        BatchingBolt and customize what mechanism causes batches to be
        processed.
        """
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

    def process(self, tup):
        """Group non-tick Tuples into batches by ``group_key``.

        .. warning::
            This method should **not** be overriden.  If you want to tweak
            how Tuples are grouped into batches, override ``group_key``.
        """
        # Append latest Tuple to batches
        group_key = self.group_key(tup)
        self._batches[group_key].append(tup)

    def _run(self):
        """The inside of ``run``'s infinite loop.

        Separated out so it can be properly unit tested.
        """
        self._current_tups = [self.read_tuple()]
        tup = self._current_tups[0]
        if self.is_heartbeat(tup):
            self.send_message({'command': 'sync'})
        elif self.is_tick(tup):
            self.process_tick(tup)
        else:
            self.process(tup)
        # reset so that we don't accidentally fail the wrong Tuples
        # if a successive call to read_tuple fails
        self._current_tups = []

    def _handle_run_exception(self, exc):
        """Process an exception encountered while running the ``run()`` loop.

        Called right before program exits.
        """
        # Don't use super here, because Bolt class has own auto fail handling.
        Component._handle_run_exception(self, exc)
        self.raise_exception(exc, self._current_tups)

        if self.auto_fail:
            # Fail batches
            for batch in itervalues(self._batches):
                for tup in batch:
                    self.fail(tup)
            # Fail current tick Tuple if we have one
            for tup in self._current_tups:
                if self.is_tick(tup):
                    self.fail(tup)


class TicklessBatchingBolt(BatchingBolt):
    """A BatchingBolt which uses a timer thread instead of tick tuples.

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
                                tuples in any batch, the TicklessBatchingBolt will
                                continue to sleep.

                                .. note::
                                  Can be fractional to specify greater
                                  precision (e.g. 2.5).

    **Example**:

    .. code-block:: python

        from streamparse.bolt import TicklessBatchingBolt

        class WordCounterBolt(TicklessBatchingBolt):

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
        super(TicklessBatchingBolt, self).__init__(*args, **kwargs)
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

    def process_tick(self, tick_tup):
        """ Just ack tick tuples and ignore them. """
        if self.auto_ack:
             self.ack(tick_tup)

    def process(self, tup):
        """Group non-tick Tuples into batches by ``group_key``.

        .. warning::
            This method should **not** be overriden.  If you want to tweak
            how Tuples are grouped into batches, override ``group_key``.
        """
        # Append latest Tuple to batches
        group_key = self.group_key(tup)
        with self._batch_lock:
            self._batches[group_key].append(tup)

    def _batch_entry_run(self):
        """The inside of ``_batch_entry``'s infinite loop.

        Separated out so it can be properly unit tested.
        """
        time.sleep(self.secs_between_batches)
        with self._batch_lock:
            self.process_batches()

    def _batch_entry(self):
        """Entry point for the batcher thread."""
        try:
            while True:
                self._batch_entry_run()
        except Exception:
            self.exc_info = sys.exc_info()
            os.kill(self.pid, signal.SIGUSR1)  # interrupt stdin waiting

    def _handle_worker_exception(self, signum, frame):
        """Handle an exception raised in the worker thread.

        Exceptions in the _batcher thread will send a SIGUSR1 to the main
        thread which we catch here, and then raise in the main thread.
        """
        reraise(*self.exc_info)


    def _handle_run_exception(self, exc):
        """Process an exception encountered while running the ``run()`` loop.

        Called right before program exits.
        """
        with self._batch_lock:
            super(TicklessBatchingBolt, self)._handle_run_exception(self, exc)
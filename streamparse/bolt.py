"""Base Bolt classes."""
from __future__ import absolute_import, print_function, unicode_literals

from collections import defaultdict
import os
import signal
import sys
import threading
import time

from six import iteritems, reraise, PY3

from .base import Component
from .ipc import (read_handshake, read_tuple, send_message, json, _stdout,
                  Tuple)


class Bolt(Component):
    """The base class for all streamparse bolts.

    For more information on bolts, consult Storm's
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

    def process(self, tup):
        """Process a single tuple :class:`Tuple` of input

        This should be overridden by subclasses.  :class:`Tuple` objects
        contain metadata about which component, stream and task it came from.
        The actual values of the tuple can be accessed by calling
        ``tup.values``.

        :param tup: the tuple to be processed.
        :type tup: Tuple
        """
        raise NotImplementedError()

    def emit(self, tup, stream=None, anchors=None, direct_task=None):
        """Emit a new tuple to a stream.

        :param tup: the Tuple payload to send to Storm, should contain only
                    JSON-serializable data.
        :type tup: list
        :param stream: the ID of the stream to emit this tuple to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param anchors: IDs of the tuples the emitted tuple should be anchored
                        to.
        :type anchors: list
        :param direct_task: the task to send the tuple to.
        :type direct_task: int
        """
        if anchors is None:
            anchors = []
        if not isinstance(tup, list):
            raise TypeError('All tuples must be lists, received {!r} instead'
                            .format(type(tup)))
        msg = {'command': 'emit', 'tuple': tup}
        if stream is not None:
            msg['stream'] = stream
        msg['anchors'] = [x.id for x in anchors]
        if direct_task is not None:
            msg['task'] = direct_task

        send_message(msg)

    def emit_many(self, tuples, stream=None, anchors=None, direct_task=None):
        """A more efficient way to send many tuples.

        Dumps out all tuples to STDOUT instead of writing one at a time.

        :param tuples: a ``list`` containing ``list`` s of tuple payload data
                       to send to Storm. All tuples should contain only
                       JSON-serializable data.
        :type tuples: list
        :param stream: the ID of the steram to emit these tuples to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param anchors: IDs the tuples which the emitted tuples should be
                        anchored to.
        :type anchors: list
        :param direct_task: indicates the task to send the tuple to.
        :type direct_task: int
        """
        if anchors is None:
            anchors = []
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
        wrapped_msg = "{}\nend\n".format("\nend\n".join(lines)).encode('utf-8')
        if PY3:
            _stdout.flush()
            _stdout.buffer.write(wrapped_msg)
        else:
            _stdout.write(wrapped_msg)
        _stdout.flush()

    def ack(self, tup):
        """Indicate that processing of a tuple has succeeded.

        :param tup: the tuple to acknowledge.
        :type tup: str or Tuple
        """
        tup_id = tup.id if isinstance(tup, Tuple) else tup
        send_message({'command': 'ack', 'id': tup_id})

    def fail(self, tup):
        """Indicate that processing of a tuple has failed.

        :param tup: the tuple to fail.
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
        tup = None
        try:
            self.initialize(storm_conf, context)
            while True:
                tup = read_tuple()
                self.process(tup)
        except Exception as e:
            self.raise_exception(e, tup)


class BasicBolt(Bolt):
    """A bolt that automatically acknowledges tuples after :func:`process`."""

    def emit(self, tup, stream=None, anchors=None, direct_task=None):
        """
        Overridden to anchor to the current tuple if no anchors are specified
        """
        if anchors is None:
            anchors = []
        anchors = anchors or [self.__current_tup]
        super(BasicBolt, self).emit(
            tup, stream=stream, anchors=anchors, direct_task=direct_task
        )

    def run(self):
        storm_conf, context = read_handshake()
        self.__current_tup = None # used for auto-anchoring
        try:
            self.initialize(storm_conf, context)
            while True:
                self.__current_tup = read_tuple()
                self.process(self.__current_tup)
                self.ack(self.__current_tup)
        except Exception as e:
            self.raise_exception(e, self.__current_tup)


class BatchingBolt(Bolt):
    """A bolt which batches tuples for processing.

    Batching tuples is unexpectedly complex to do correctly. The main problem
    is that all bolts are single-threaded. The difficult comes when the
    topology is shutting down because Storm stops feeding the bolt tuples. If
    the bolt is blocked waiting on stdin, then it can't process any waiting
    tuples, or even ack ones that were asynchronously written to a data store.

    This bolt helps with that grouping tuples based on a time interval and then
    processing them on a worker thread. The bolt also handles ack'ing tuples
    after processing has finished, much like the BasicBolt.

    To use this class, you must implement ``process_batch``. ``group_key`` can
    be optionally implemented so that tuples are grouped before
    ``process_batch`` is even called.
    """
    SECS_BETWEEN_BATCHES = 2

    def __init__(self):
        self.exc_info = None
        signal.signal(signal.SIGINT, self._handle_worker_exception)

        self._batch = defaultdict(list)
        self._should_stop = threading.Event()
        self._batcher = threading.Thread(target=self._batch_entry)
        self._batch_lock = threading.Lock()
        self._batcher.daemon = True
        self._batcher.start()

    def process(self, tup):
        """Add a tuple a specific batch by group key. Do not override this
        method in subclasses.
        """
        with self._batch_lock:
            group_key = self.group_key(tup)
            self._batch[group_key].append(tup)

    def group_key(self, tup):
        """Return the group key used to group tuples within a batch.

        By default, returns None, which put all tuples in a single
        batch. Override this function to enable batching.

        :param tup: the tuple used to extract a group key
        :type tup: Tuple
        :returns: Any ``hashable`` value (will be used in a ``dict``).
        """
        return None

    def process_batch(self, key, tups):
        """Process a batch of tuples. Should be overridden by subclasses.

        :param key: the group key for the list of batches.
        :type key: hashable
        :param tups: a `list` of :class:`ipc.Tuple` for the group.
        :type tups: list
        """
        raise NotImplementedError()

    def _batch_entry(self):
        """Entry point for the batcher thread."""
        try:
            while True:
                time.sleep(self.SECS_BETWEEN_BATCHES)
                with self._batch_lock:
                    if not self._batch:
                        # No tuples to save
                        continue
                    for key, tups in iteritems(self._batch):
                        self.process_batch(key, tups)
                        for tup in tups:
                            self.ack(tup)
                    self._batch = defaultdict(list)
        except Exception:
            self.exc_info = sys.exc_info()
            os.kill(os.getpid(), signal.SIGINT)  # interrupt stdin waiting

    def _handle_worker_exception(self, signum, frame):
        """Handle an exception raised in the worker thread.

        Exceptions in the _batcher thread will send a SIGINT to the main
        thread which we catch here, and then raise in the main thread.
        """
        reraise(*self.exc_info)

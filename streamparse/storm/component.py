"""Base primititve classes for working with Storm."""
from __future__ import absolute_import, print_function, unicode_literals

import io
import logging
import os
import sys
from collections import deque, namedtuple
from logging.handlers import RotatingFileHandler
from os.path import join
from threading import RLock
from traceback import format_exc

try:
    import simplejson as json
except ImportError:
    import json


# Support for Storm Log levels as per STORM-414
_STORM_LOG_TRACE = 0
_STORM_LOG_DEBUG = 1
_STORM_LOG_INFO = 2
_STORM_LOG_WARN = 3
_STORM_LOG_ERROR = 4
_STORM_LOG_LEVELS = {
    'trace': _STORM_LOG_TRACE,
    'debug': _STORM_LOG_DEBUG,
    'info': _STORM_LOG_INFO,
    'warn': _STORM_LOG_WARN,
    'warning': _STORM_LOG_WARN,
    'error': _STORM_LOG_ERROR,
    'critical': _STORM_LOG_ERROR
}
_PYTHON_LOG_LEVELS = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'warn': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'trace': logging.DEBUG
}


log = logging.getLogger(__name__)


class StormHandler(logging.Handler):
    """Handler that will send messages back to Storm."""

    def __init__(self, stream=None):
        """ Initialize handler """
        if stream is None:
            stream = sys.stdout
        super(StormHandler, self).__init__()
        self._component = Component(output_stream=stream)

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        If exception information is present, it is formatted using
        traceback.print_exception and sent to Storm.
        """
        try:
            msg = self.format(record)
            level = _STORM_LOG_LEVELS.get(record.levelname.lower(),
                                          _STORM_LOG_INFO)
            self._component.send_message({'command': 'log', 'msg': str(msg),
                                          'level': level})
        except Exception:
            self.handleError(record)


class LogStream(object):
    """Object that implements enough of the Python stream API to be used as
    sys.stdout. Messages are written to the Python logger.
    """
    def __init__(self, logger):
        self.logger = logger

    def write(self, message):
        if message.strip() == "":
            return  # skip blank lines

        try:
            self.logger.info(message)
        except:
            # There's been an issue somewhere in the logging sub-system
            # so we'll put stderr and stdout back to their originals and
            # raise the exception which will cause Storm to choke
            sys.stdout = sys.__stdout__
            raise

    def flush(self):
        """No-op method to prevent crashes when someone does
        sys.stdout.flush.
        """
        pass


Tuple = namedtuple('Tuple', 'id component stream task values')
"""Storm's primitive data type passed around via streams.

:ivar id: the ID of the tuple.
:type id: str
:ivar component: component that the tuple was generated from.
:type component: str
:ivar stream: the stream that the tuple was emitted into.
:type stream: str
:ivar task: the task the tuple was generated from.
:type task: int
:ivar values: the payload of the tuple where data is stored.
:type values: list
"""


class Component(object):
    """Base class for Spouts and Bolts which contains class methods for
    logging messages back to the Storm worker process.


    :ivar input_stream: The ``file``-like object to use to retrieve commands
                        from Storm.  Defaults to ``sys.stdin``.
    :ivar output_stream: The ``file``-like object to send messages to Storm with.
                         Defaults to ``sys.stdout``.
    :ivar topology_name: The name of the topology sent by Storm in the initial
                         handshake.
    :ivar task_id: The numerical task ID for this component, as sent by Storm in
                   the initial handshake.
    :ivar component_name: The name of this component, as sent by Storm in the
                          initial handshake.
    :ivar debug: A ``bool`` indicating whether or not Storm is running in debug
                 mode.  Specified by the `topology.debug` Storm setting.
    :ivar storm_conf: A ``dict`` containing the configuration values sent by
                      Storm in the initial handshake with this component.
    :ivar context: The context of where this component is in the topology.  See
                   `the Storm Multi-Lang protocol documentation <https://storm.apache.org/documentation/Multilang-protocol.html>`__
                   for details.
    :ivar pid: An ``int`` indicating the process ID of this component as
               retrieved by ``os.getpid()``.
    :ivar logger: A logger to use with this component.

                  .. note::
                    Using ``Component.logger`` combined with the
                    :class:`streamparse.storm.component.StormHandler` handler is
                    the recommended way for logging messages from your
                    component. If you use ``Component.log`` instead, the logging
                    messages will *always* be sent to Storm, even if they are
                    ``debug`` level messages and you are running in production.
                    Using :class:`streamparse.storm.component.StormHandler`
                    ensures that you will instead have your logging messages
                    filtered on the Python side and only have the messages you
                    actually want logged serialized and sent to Storm.
    """


    def __init__(self, input_stream=sys.stdin, output_stream=sys.stdout):
        # Ensure we don't fall back on the platform-dependent encoding and always
        # use UTF-8 https://docs.python.org/3.4/library/sys.html#sys.stdin
        if hasattr(input_stream, 'buffer'):
            input_stream = io.TextIOWrapper(input_stream.buffer,
                                            encoding='utf-8')
        self.input_stream = input_stream
        # Python 2 stdout does not have buffer, and neither would a StringIO
        # object like nose replaces sys.stdout with
        if hasattr(output_stream, 'buffer'):
            output_stream = output_stream.buffer
        self.output_stream = output_stream
        self.topology_name = None
        self.task_id = None
        self.component_name = None
        self.debug = None
        self.storm_conf = None
        self.context = None
        self.pid = os.getpid()
        self.logger = None
        # pending commands/tuples we read while trying to read task IDs
        self._pending_commands = deque()
        # pending task IDs we read while trying to read commands/tuples
        self._pending_task_ids = deque()
        self._reader_lock = RLock()
        self._writer_lock = RLock()

    def _setup_component(self, storm_conf, context):
        """Add helpful instance variables to component after initial handshake
        with Storm.  Also configure logging.
        """
        self.topology_name = storm_conf.get('topology.name', '')
        self.task_id = context.get('taskid', '')
        self.component_name = context.get('task->component', {})\
                                      .get(str(self.task_id), '')
        self.debug = storm_conf.get("topology.debug", False)
        self.storm_conf = storm_conf
        self.context = context
        self.logger = logging.getLogger('.'.join((__name__,
                                                  self.component_name)))
        # Set up logging
        log_path = self.storm_conf.get('streamparse.log.path')
        if log_path:
            root_log = logging.getLogger()
            max_bytes = self.storm_conf.get('streamparse.log.max_bytes',
                                            1000000)  # 1 MB
            backup_count = self.storm_conf.get('streamparse.log.backup_count',
                                               10)
            log_file = join(log_path,
                            ('streamparse_{topology_name}_{component_name}'
                             '_{task_id}_{pid}.log'
                             .format(topology_name=self.topology_name,
                                     component_name=self.component_name,
                                     task_id=self.task_id,
                                     pid=self.pid)))
            handler = RotatingFileHandler(log_file, maxBytes=max_bytes,
                                          backupCount=backup_count)
            formatter = logging.Formatter('%(asctime)s - %(name)s - '
                                          '%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            root_log.addHandler(handler)
            log_level = self.storm_conf.get('streamparse.log.level', 'info')
            log_level = _PYTHON_LOG_LEVELS.get(log_level, logging.INFO)
            if self.debug:
                # potentially override logging that was provided if
                # topology.debug was set to true
                log_level = logging.DEBUG
            root_log.setLevel(log_level)
        else:
            self.send_message({'command': 'log',
                               'msg': ('WARNING: streamparse logging is not '
                                       'configured. Please set streamparse.log.'
                                       'path in your config.json.')})
        # Redirect stdout to ensure that print statements/functions
        # won't disrupt the multilang protocol
        sys.stdout = LogStream(logging.getLogger('streamparse.stdout'))

    def read_message(self):
        """Read a message from Storm, reconstruct newlines appropriately.

        All of Storm's messages (for either Bolts or Spouts) should be of the
        form::

            '<command or task_id form prior emit>\\nend\\n'

        Command example, an incoming tuple to a bolt::

            '{ "id": "-6955786537413359385",  "comp": "1", "stream": "1", "task": 9, "tuple": ["snow white and the seven dwarfs", "field2", 3]}\\nend\\n'

        Command example for a Spout to emit it's next tuple::

            '{"command": "next"}\\nend\\n'

        Example, the task IDs a prior emit was sent to::

            '[12, 22, 24]\\nend\\n'

        The edge case of where we read ``''`` from ``input_stream`` indicating
        EOF, usually means that communication with the supervisor has been
        severed.
        """
        msg = ""
        num_blank_lines = 0
        while True:
            # readline will return trailing \n so that output is unambigious, we
            # should only have line == '' if we're at EOF
            with self._reader_lock:
                line = self.input_stream.readline()
            if line == 'end\n':
                break
            elif line == '':
                log.error("Received EOF while trying to read stdin from Storm, "
                           "pipe appears to be broken, exiting.")
                sys.exit(1)
            elif line == '\n':
                num_blank_lines += 1
                if num_blank_lines % 1000 == 0:
                    log.warn("While trying to read a command or pending task "
                             "ID, Storm has instead sent %s '\\n' messages.",
                             num_blank_lines)
                continue

            msg = '{}{}\n'.format(msg, line[0:-1])

        try:
            return json.loads(msg)
        except Exception:
            log.error("JSON decode error for message: %r", msg, exc_info=True)
            raise

    def read_task_ids(self):
        if self._pending_task_ids:
            return self._pending_task_ids.popleft()
        else:
            msg = self.read_message()
            while not isinstance(msg, list):
                self._pending_commands.append(msg)
                msg = self.read_message()
            return msg

    def read_command(self):
        if self._pending_commands:
            return self._pending_commands.popleft()
        else:
            msg = self.read_message()
            while isinstance(msg, list):
                self._pending_task_ids.append(msg)
                msg = self.read_message()
            return msg

    def read_tuple(self):
        cmd = self.read_command()
        return Tuple(cmd['id'], cmd['comp'], cmd['stream'], cmd['task'],
                     cmd['tuple'])

    def read_handshake(self):
        """Read and process an initial handshake message from Storm."""
        msg = self.read_message()
        pid_dir, _conf, _context = msg['pidDir'], msg['conf'], msg['context']

        # Write a blank PID file out to the pidDir
        open(join(pid_dir, str(self.pid)), 'w').close()
        self.send_message({'pid': self.pid})

        return _conf, _context

    def send_message(self, message):
        """Send a message to Storm via stdout."""
        if not isinstance(message, dict):
            log.error("%s.%d attempted to send a non dict message to Storm: %r",
                       self.component_name, self.pid, message)
            return

        wrapped_msg = "{}\nend\n".format(json.dumps(message)).encode('utf-8')

        with self._writer_lock:
            self.output_stream.flush()
            self.output_stream.write(wrapped_msg)
            self.output_stream.flush()

    def raise_exception(self, exception, tup=None):
        """Report an exception back to Storm via logging.

        :param exception: a Python exception.
        :param tup: a :class:`Tuple` object.
        """
        if tup:
            message = ('Python {exception_name} raised while processing tuple '
                       '{tup!r}\n{traceback}')
        else:
            message = 'Python {exception_name} raised\n{traceback}'
        message = message.format(exception_name=exception.__class__.__name__,
                                 tup=tup,
                                 traceback=format_exc())
        self.send_message({'command': 'error', 'msg': str(message)})
        self.send_message({'command': 'sync'})  # sync up right away

    def log(self, message, level=None):
        """Log a message to Storm optionally providing a logging level.

        :param message: the log message to send to Storm.
        :type message: str
        :param level: the logging level that Storm should use when writing the
                      ``message``. Can be one of: trace, debug, info, warn, or
                      error (default: ``info``).
        :type level: str

        .. warning::

          This will send your message to Storm regardless of what level you
          specify.  In almost all cases, you are better of using
          ``Component.logger`` with a
          :class:`streamparse.storm.component.StormHandler`, because the
          filtering will happen on the Python side (instead of on the Java side
          after taking the time to serialize your message and send it to Storm).
        """
        level = _STORM_LOG_LEVELS.get(level, _STORM_LOG_INFO)
        self.send_message({'command': 'log', 'msg': str(message),
                           'level': level})

    def emit(self, tup, tup_id=None, stream=None, anchors=None,
             direct_task=None, need_task_ids=True):
        """Emit a new tuple to a stream.

        :param tup: the Tuple payload to send to Storm, should contain only
                    JSON-serializable data.
        :type tup: :class:`list` or :class:`streamparse.storm.component.Tuple`
        :param tup_id: the ID for the tuple. If omitted by a
                       :class:`streamparse.storm.spout.Spout`, this emit will be
                       unreliable.
        :type tup_id: str
        :param stream: the ID of the stream to emit this tuple to. Specify
                       ``None`` to emit to default stream.
        :type stream: str
        :param anchors: IDs the tuples (or :class:`streamparse.storm.component.Tuple`
                        instances) which the emitted tuples should be anchored
                        to. If ``auto_anchor`` is set to ``True`` and
                        you have not specified ``anchors``, ``anchors`` will be
                        set to the incoming/most recent tuple ID(s).  This is
                        only passed by :class:`streamparse.storm.bolt.Bolt`.
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

        if anchors is not None:
            msg['anchors'] = anchors
        if tup_id is not None:
            msg['id'] = tup_id
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

    def run(self):
        """Main run loop for all components.

        Performs initial handshake with Storm and reads tuples handing them off
        to subclasses.  Any exceptions are caught and logged back to Storm
        prior to the Python process exiting.

        .. warning::

            Subclasses should **not** override this method.
        """
        storm_conf, context = self.read_handshake()
        self._setup_component(storm_conf, context)

        try:
            self.initialize(storm_conf, context)
            while True:
                self._run()
        except Exception as e:
            self._handle_run_exception(e)
            sys.exit(1)

    def _handle_run_exception(self, exc):
        """Process an exception encountered while running the ``run()`` loop.

        Called right before program exits.
        """
        log_msg = "Exception in {}.run()".format(self.__class__.__name__)
        log.error(log_msg, exc_info=True)
        self.raise_exception(exc)


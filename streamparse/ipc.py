"""
Utilities for interprocess communication between Python and Storm.
"""
from __future__ import absolute_import, print_function, unicode_literals

try:
    import simplejson as json
except ImportError:
    import json
import logging
import logging.handlers
import os
import sys
from collections import deque
from threading import RLock

from six import PY3


# Module globals
_PYTHON_LOG_LEVELS = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}
_log = logging.getLogger('streamparse.ipc')
# pending commands/tuples we read while trying to read task IDs
_pending_commands = deque()
# pending task IDs we read while trying to read commands/tuples
_pending_task_ids = deque()
_pid = os.getpid()
_debug = False
_topology_name = _component_name = _task_id = _conf = _context = None
_reader_lock = RLock()
_writer_lock = RLock()

# Setup stdin line reader and stdout
if PY3:
    # Ensure we don't fall back on the platform-dependent encoding and always
    # use UTF-8 https://docs.python.org/3.4/library/sys.html#sys.stdin
    import io
    _readline = io.TextIOWrapper(sys.stdin.buffer,
                                 encoding='utf-8').readline
else:
    def _readline():
        line = sys.stdin.readline()
        return line.decode('utf-8')

_stdout = sys.stdout
# Travis CI has stdout set to an io.StringIO object instead of an
# io.BufferedWriter object which is what's actually used when streamparse is
# running
if hasattr(sys.stdout, 'buffer'):
    _stdout = sys.stdout.buffer
else:
    _stdout = sys.stdout


class LogStream(object):
    """Object that implements enough of the Python stream API to be used as
    sys.stdout and sys.stderr. Messages are written to the Python logger.
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
            sys.stderr = sys.__stderr__
            raise


class Tuple(object):
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

    __slots__ = ['id', 'component', 'stream', 'task', 'values']

    def __init__(self, id, component, stream, task, values):
        self.id = id
        self.component = component
        self.stream = stream
        self.task = task
        self.values = values

    def __repr__(self):
        return ('Tuple(id={!r}, component={!r}, stream={!r}, task={!r}, '
                'values={!r})'
                .format(self.id, self.component, self.stream, self.task,
                        self.values))


# Message recieving

def read_message():
    """Read a message from Storm, reconstruct newlines appropriately.

    All of Storm's messages (for either Bolts or Spouts) should be of the form:

    '<command or task_id form prior emit>\nend\n'

    Command example, an incoming tuple to a bolt:
    '{ "id": "-6955786537413359385",  "comp": "1", "stream": "1", "task": 9, "tuple": ["snow white and the seven dwarfs", "field2", 3]}\nend\n'

    Command example for a Spout to emit it's next tuple:
    '{"command": "next"}\nend\n'

    Example, the task IDs a prior emit was sent to:
    '[12, 22, 24]\nend\n'

    The edge case of where we read '' from _readline indicating EOF, usually
    means that communication with the supervisor has been severed.
    """
    msg = ""
    num_blank_lines = 0
    while True:
        # readline will return trailing \n so that output is unambigious, we
        # should only have line == '' if we're at EOF
        with _reader_lock:
            line = _readline()

        if line == 'end\n':
            break
        elif line == '':
            _log.error("Received EOF while trying to read stdin from Storm, "
                       "pipe appears to be broken, exiting.")
            sys.exit(1)
        elif line == '\n':
            num_blank_lines += 1
            if num_blank_lines % 1000 == 0:
                _log.warn("While trying to read a command or pending task ID, "
                          "Storm has instead sent {:,} '\\n' messages."
                          .format(num_blank_lines))
            continue

        msg = '{}{}\n'.format(msg, line[0:-1])

    try:
        return json.loads(msg)
    except Exception:
        _log.error("JSON decode error for message: %r", msg, exc_info=True)
        raise


def read_task_ids():
    if _pending_task_ids:
        return _pending_task_ids.popleft()
    else:
        msg = read_message()
        while not isinstance(msg, list):
            _pending_commands.append(msg)
            msg = read_message()
        return msg


def read_command():
    if _pending_commands:
        return _pending_commands.popleft()
    else:
        msg = read_message()
        while isinstance(msg, list):
            _pending_task_ids.append(msg)
            msg = read_message()
        return msg


def read_tuple():
    cmd = read_command()
    return Tuple(cmd['id'], cmd['comp'], cmd['stream'], cmd['task'],
                 cmd['tuple'])


def read_handshake():
    """Read and process an initial handshake message from Storm."""
    global _topology_name, _component_name, _task_id, _conf, _context, _debug

    msg = read_message()
    pid_dir, _conf, _context = msg['pidDir'], msg['conf'], msg['context']

    # Write a blank PID file out to the pidDir
    open('{}/{}'.format(pid_dir, str(_pid)), 'w').close()
    send_message({'pid': _pid})

    # Set up globals
    _topology_name = _conf.get('topology.name', '')
    _task_id = _context.get('taskid', '')
    _component_name = _context.get('task->component', {}).get(str(_task_id), '')
    _debug = _conf.get('topology.debug', False)

    # Set up logging
    log_path = _conf.get('streamparse.log.path')
    if log_path:
        root_log = logging.getLogger()
        max_bytes = _conf.get('stremparse.log.max_bytes', 1000000)  # 1 MB
        backup_count = _conf.get('streamparse.log.backup_count', 10)
        log_file = ('{log_path}/streamparse_{topology_name}_{component_name}_'
                    '{task_id}_{pid}.log'
                    .format(log_path=log_path, topology_name=_topology_name,
                            component_name=_component_name, task_id=_task_id,
                            pid=_pid))
        handler = logging.handlers.RotatingFileHandler(log_file,
                                                       maxBytes=max_bytes,
                                                       backupCount=backup_count)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root_log.addHandler(handler)
        log_level = _conf.get('streamparse.log.level', 'info')
        log_level = _PYTHON_LOG_LEVELS.get(log_level, logging.INFO)
        if _debug:
            # potentially override logging that was provided if topology.debug
            # was set to true
            log_level = logging.DEBUG
        root_log.setLevel(log_level)
    else:
        send_message({
            'command': 'log',
            'msg': ('WARNING: streamparse logging is not configured. Please '
                    'set streamparse.log.path in you config.json.')})

    # Redirect stdout and stderr to ensure that print statements/functions
    # won't disrupt the multilang protocol
    sys.stdout = LogStream(logging.getLogger('streamparse.stdout'))
    sys.stderr = LogStream(logging.getLogger('streamparse.stderr'))

    _log.info('Received initial handshake message from Storm\n%r', msg)
    _log.info('Process ID (%d) sent to Storm', _pid)

    return _conf, _context


# Message sending

def send_message(message):
    """Send a message to Storm via stdout."""
    if not isinstance(message, dict):
        _log.error("%s.%d attempted to send a non dict message to Storm: %r",
                   _component_name, _pid, message)
        return

    wrapped_msg = "{}\nend\n".format(json.dumps(message)).encode('utf-8')

    with _writer_lock:
        _stdout.flush()
        _stdout.write(wrapped_msg)
        _stdout.flush()

"""
Both ends of this protocol use a line-reading mechanism, so be sure to trim off newlines from the input and to append them to your output.
All JSON inputs and outputs are terminated by a single line containing "end". Note that this delimiter is not itself JSON encoded.
The bullet points below are written from the perspective of the script writer's STDIN and STDOUT.
"""
from __future__ import print_function
try:
    import simplejson as json
except ImportError:
    import json
import logging
import os
import sys
from collections import deque
import traceback


config = context = None
storm_log = logging.getLogger('pystorm')

_MAX_MESSAGE_SIZE = 16777216
_MAX_BLANK_MSGS = 500
_MAX_LINES = 100
# queue up commands we read while trying to read task IDs
_pending_commands = deque()
# queue up task IDs we read while trying to read commands/tuples
_pending_task_ids = deque()
# we'll redirect stdout, but we'll save original for communication to Storm
_stdout = sys.stdout


class StormIPCException(Exception): pass


class LogStream(object):
    """Object that implements enough of the Python stream API to be used as
    sys.stdout and sys.stderr. Messages are written to the Python logger.
    """
    def __init__(self, logger):
        self.logger = logger

    def write(self, message):
        for line in message.split('\n'):
            self.logger.error(line)


## Message recieving

def read_message_lines():
    lines = blank_lines = 0

    while True:
        line = sys.stdin.readline()[0:-1]  # ignore new line
        if line == 'end':
            break
        lines += 1
        message_size = len(line)

        # If message size exceeds MAX_MESSAGE_SIZE, we assume that the
        # Storm worker has died, and we would be reading an infinite
        # series of blank lines. Throw an error to halt processing,
        # otherwise the task will use 100% CPU and will quickly consume
        # a huge amount of RAM.
        if message_size >= _MAX_MESSAGE_SIZE:
            raise StormIPCException(('Message {} exceeds '
                                     '{:,}'.format(line, _MAX_MESSAGE_SIZE)))

        # If Storm starts to send us a series of blank lines, after awhile we
        # have to assume that the pipe to the Storm supervisor is broken, this
        # is one of the more annoying parts of Petrel and we should probably
        # tune _MAX_BLANK_MSGS
        if line == '':
            blank_lines += 1
            if blank_lines >= _MAX_BLANK_MSGS:
                raise StormIPCException(('{:,} blank lines received, assuming '
                                         'pipe to Storm supervisor is '
                                         'broken'.format(blank_lines)))

        if lines >= _MAX_LINES:
            raise StormIPCException(('Message exceeds {:,} lines, assuming this'
                                     'is an error.'.format(lines)))

        yield line


def read_message():
    """Read a message from Storm, reconstruct newlines appropriately."""
    message = ''.join('{}\n'.format(line) for line in read_message_lines())
    return json.loads(message)


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
    return Tuple(cmd['id'], cmd['comp'], cmd['stream'], cmd['task'], cmd['tuple'])


def read_handshake():
    """Read and process an initial handshake message from Storm."""
    # Redirect stdout and stderr to ensure that print statements/functions
    # won't crash the Storm Java worker
    sys.stdout = LogStream(logging.getLogger('pystorm.stdout'))
    sys.stderr = LogStream(logging.getLogger('pystorm.stderr'))

    msg = read_message()
    storm_log.info('Received initial handshake from Storm: %r', msg)
    # Write a blank PID file out to the pidDir
    pid_dir = msg['pidDir']
    pid = os.getpid()
    open('{}/{}'.format(pid_dir, str(pid)), 'w').close()
    send_message({'pid': pid})
    storm_log.info('Process ID sent to Storm')

    return msg['conf'], msg['context']


## Message sending

def send_message(message):
    """Send a message to Storm via stdout"""
    print(json.dumps(message), file=_stdout)
    print('end', file=_stdout)
    _stdout.flush()


class Component(object):
    """Base class for Spouts and Bolts which contains class methods for
    logging messages back to the Storm worker process.
    """

    def raise_exception(self, exception):
        """Report an exception back to Storm.

        :param exception: a Python exception.
        """
        self.log('Python exception raised: {}\n{}'\
                 .format(exception.__class__.__name__,
                         traceback.format_exc(exception)))
        send_message({'command': 'sync'})  # sync up right away

    def log(self, message, level='info'):
        """Log a message to Storm optionally providing a logging level.

        :param message: any object that supports ``__str__()``.
        :param level: a ``str`` representing the log level.
        """
        send_message({'command': 'log', 'msg': str(message), 'level': level})


class Tuple(object):

    __slots__ = ['id', 'component', 'stream', 'task', 'values']

    def __init__(self, id, component, stream, task, values):
        self.id = id
        self.component = component
        self.stream = stream
        self.task = task
        self.values = values

    def __repr__(self):
        return '<{}: {}> {}'.format(self.__class__.__name__, self.id,
                                    self.values)


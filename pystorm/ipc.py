import os
import socket
import sys
import logging
import time
import traceback

from collections import deque

log = logging.getLogger(__name__)
stdout = sys.stdout

class StormIPCException(Exception):
    pass


class LogStream(object):
    """Logging class to mimic stdin/out so we don't mess up Storm IPC

    """
    def __init__(self, logger):
        self.logger = logger

    def write(self, message):
        self.logger.info(message)


def initialize():
    """Read initialization message and perform init tasks

    Redirects stdin/stderr to loggers so print statements
    don't mess up communications with storm.

    :returns: (conf, context) from storm
    """
    sys.stdout = LogStream(logging.getLogger('storm.stdout'))
    sys.stderr = LogStream(logging.getLogger('storm.stderr'))

    setup = read()
    log.info('Task config: %s', setup['conf'])
    log.info('Task context: %s', setup['context'])

    # Write the pidfile and tell Storm about it
    send_pid(setup['pidDir'])

    return setup['conf'], setup['context']


##
## Basic i/o
##

def read(max_message_lines=100,
          max_message_size=16777216,
          max_blank_lines=20):
    """Read an incoming message from Storm"""
    def line_gen():
        """Generator to read lines from stdin"""
        blank_lines = 0
        line_count = 0
        message_size = 0
        while True:
            line = sys.stdin.readline()
            if line == "end\n":
                break
            line_count += 1

            # Check 1. If message_size gets too large, we're probably reading
            # blank lines from a dead IPC connection.
            message_size += len(line)
            if max_message_size and message_size > max_message_size:
                raise StormIPCException('Message size exceeds maximum (%i). '
                                        'Assuming IPC connection dead' % message_size)

            # Check 2. A great number of blank lines also indicates the IPC
            # conneciton is dead
            if not line:
                blank_lines += 1
                storm_log.debug('Message line #%d is blank. %i blank '
                                'lines so far.' % (line_count, blank_lines))
                if max_blank_lines and blank_lines > max_blank_lines:
                    raise StormIPCException(
                        'Blank lines exceeds maximum (%i). Assuming IPC '
                        'connection dead' % max_blank_lines
                    )
            # Check 3. Maximum number of overall lines could be a problem
            if line_count > 100:
                raise StormIPCException(
                    'Message lines exceeds maximum (%i). Assuming IPC '
                    'connection dead' % max_message_lines
                )

            # Looks good
            yield line

    msg = ''.join(line for line in line_gen())
    log.debug('stdin: %s', msg)
    return json.loads(msg)


def write(msg):
    msg = json.dumps(msg)
    stdout.write(msg)
    stdout.write('\nend\n') # \n at start avoids an unnecessary string copy
    try:
        stdout.flush()
    except (IOError, OSError) as e:
        log.exception(str(e))
        raise StormIPCException('%s error [Errno %d] in sendMsgToParent: %s' % (
            type(e).__name__,
            e.errno,
            str(e)))
    log.debug('stdout: %s', msg)


##
## Command implementations
##

def send_ack(tup):
    """ACK a Tuple"""
    write({"command": "ack", "id": tup.id})

def send_error(msg):
    """Send error message to Storm"""
    write({"command": "error", "msg": msg})

def send_fail(tup):
    """Fail a tuple"""
    write({"command": "fail", "id": tup.id})

def send_log(msg):
    write({"command": "log", "msg": msg})

def send_pid(pid_dir):
    """Write pidfile and send pid to Storm"""
    pid = os.getpid()
    open(os.path.join(pid_dir, str(pid)), "w").close()
    write({'pid':pid})
    log.info('Task pid sent to Storm')

def send_sync():
    write({'command':'sync'})

################################################################################
################################################################################
################################################################################
################################################################################
################################################################################

#queue up commands we read while trying to read taskids
pending_commands = deque()

def readTaskIds():
    if pending_taskids:
        return pending_taskids.popleft()
    else:
        msg = readMsg()
        while type(msg) is not list:
            pending_commands.append(msg)
            msg = readMsg()
        return msg

#queue up taskids we read while trying to read commands/tuples
pending_taskids = deque()

def readCommand():
    if pending_commands:
        return pending_commands.popleft()
    else:
        msg = readMsg()
        while type(msg) is list:
            pending_taskids.append(msg)
            msg = readMsg()
        return msg

def readTuple():
    cmd = readCommand()
    return Tuple(cmd["id"], cmd["comp"], cmd["stream"], cmd["task"], cmd["tuple"])

def sendMsgToParent(msg):
    print >> old_stdout, json_encode(msg)
    print >> old_stdout, "end"
    try:
        old_stdout.flush()
    except (IOError, OSError) as e:
        storm_log.exception(str(e))
        raise StormIPCException('%s error [Errno %d] in sendMsgToParent: %s' % (
            type(e).__name__,
            e.errno,
            str(e)))

# This function is probably obsolete with the addition of the new
# reportError() function.
# TODO: Consider getting rid of this function and call reportError() instead.
# However, need to consider the case where we are running on an older version
# of Storm where the Storm back end does not support reportError()? Can we
# detect that case and use this function instead?
def sendFailureMsgToParent(msg):
    """This function is kind of a hack, but useful when a Python task
    encounters a fatal exception. "msg" should be a simple string like
    "E_SPOUTFAILED". This function sends "msg" as-is to the Storm worker,
    which tries to parse it as JSON. The hacky aspect is that we
    *deliberately* make it fail by sending it non-JSON data. This causes
    the Storm worker to throw an error and restart the Python task. This
    is cleaner than simply letting the task die without notifying Storm,
    because this way Storm restarts the task more quickly."""
    assert isinstance(msg, basestring)
    print >> old_stdout, msg
    print >> old_stdout, "end"
    storm_log.error('Sent failure message ("%s") to Storm', msg)


def emit(*args, **kwargs):
    result = __emit(*args, **kwargs)
    if result:
        return readTaskIds()

def emitMany(*args, **kwargs):
    """A more efficient way to emit a number of tuples at once."""
    global MODE
    if MODE == Bolt:
        emitManyBolt(*args, **kwargs)
    elif MODE == Spout:
        emitManySpout(*args, **kwargs)

def emitDirect(task, *args, **kwargs):
    kwargs["directTask"] = task
    __emit(*args, **kwargs)

def __emit(*args, **kwargs):
    global MODE
    if MODE == Bolt:
        return emitBolt(*args, **kwargs)
    elif MODE == Spout:
        return emitSpout(*args, **kwargs)

def emitManyBolt(tuples, stream=None, anchors = [], directTask=None):
    global ANCHOR_TUPLE
    if ANCHOR_TUPLE is not None:
        anchors = [ANCHOR_TUPLE]
    m = {
        "command": "emit",
        "anchors": [a.id for a in anchors],
        "tuple": None,
        "need_task_ids": False,
    }
    if stream is not None:
        m["stream"] = stream
    if directTask is not None:
        m["task"] = directTask

    lines = []
    for tup in tuples:
        m["tuple"] = tup
        lines.append(json_encode(m))
        lines.append('end')
    print >> old_stdout, '\n'.join(lines)

def emitBolt(tup, stream=None, anchors = [], directTask=None, need_task_ids=False):
    global ANCHOR_TUPLE
    if ANCHOR_TUPLE is not None:
        anchors = [ANCHOR_TUPLE]
    m = {
        "command": "emit",
        "anchors": [a.id for a in anchors],
        "tuple": tup,
        "need_task_ids": need_task_ids,
    }
    if stream is not None:
        m["stream"] = stream
    if directTask is not None:
        m["task"] = directTask
    sendMsgToParent(m)
    return need_task_ids

def emitManySpout(tuples, stream=None, id=None, directTask=None):
    m = {
        "command": "emit",
        "tuple": None,
        "need_task_ids": need_task_ids,
    }
    if id is not None:
        m["id"] = id
    if stream is not None:
        m["stream"] = stream
    if directTask is not None:
        m["task"] = directTask

    lines = []
    for tup in tuples:
        m["tuple"] = tup
        lines.append(json_encode(m))
        lines.append('end')
    print >> old_stdout, '\n'.join(lines)

def emitSpout(tup, stream=None, id=None, directTask=None, need_task_ids=False):
    m = {
        "command": "emit",
        "tuple": tup,
        "need_task_ids": need_task_ids,
    }
    if id is not None:
        m["id"] = id
    if stream is not None:
        m["stream"] = stream
    if directTask is not None:
        m["task"] = directTask
    sendMsgToParent(m)
    return need_task_ids

def ackId(tupid):
    """Acknowledge a tuple when you only have its ID"""
    sendMsgToParent({"command": "ack", "id": tupid})


def initialize_profiling():
    global TUPLE_PROFILING
    TUPLE_PROFILING = storm_log.isEnabledFor(logging.DEBUG)
    if TUPLE_PROFILING:
        storm_log.info('Tuple profiling enabled. Will log tuple processing times.')
    else:
        storm_log.info('Tuple profiling NOT enabled. Will not log tuple processing times.')

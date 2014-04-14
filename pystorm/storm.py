import sys
import os
import time
import socket
import logging
import traceback
from collections import deque

try:
    # Use simplejson instead of json because it is released more frequently and
    # is generally faster.
    import simplejson as json

    # However, if speedups are not installed, simplejson will be slow, so use
    # the built-in json instead.
    if json._import_c_make_encoder() is None:
        import json
except ImportError:
    import json

storm_log = logging.getLogger('storm')

TUPLE_PROFILING = False

json_encode = lambda x: json.dumps(x)
json_decode = lambda x: json.loads(x)

BLANK_LINE_CHECK = True

# Save old stdout so we can still write to it after redirecting.
old_stdout = sys.stdout

# TODO: Get this value from a topology configuration setting.
MAX_MESSAGE_SIZE = 16777216

class StormIPCException(Exception):
    pass

#reads lines and reconstructs newlines appropriately
def readMsg():
    def read_message_lines():
        if BLANK_LINE_CHECK:
            count_blank = 0
        i_line = 0
        message_size = 0
        while True:
            line = sys.stdin.readline()[0:-1]
            i_line += 1
            message_size += len(line)
            if line == "end":
                break
            # If message size exceeds MAX_MESSAGE_SIZE, we assume that the Storm
            # worker has died, and we would be reading an infinite series of blank
            # lines. Throw an error to halt processing, otherwise the task will
            # use 100% CPU and will quickly consume a huge amount of RAM.
            if MAX_MESSAGE_SIZE is not None and message_size > MAX_MESSAGE_SIZE:
                raise StormIPCException('Message exceeds MAX_MESSAGE_SIZE -- assuming this is an error')

            if BLANK_LINE_CHECK:
                if not line:
                    storm_log.debug('Message line #%d is blank. Pipe to Storm supervisor may be broken.', i_line)
                    count_blank += 1
                    if count_blank >= 20:
                        raise StormIPCException('Pipe to Storm supervisor seems to be broken!')
                if i_line > 100:
                    raise StormIPCException('Message exceeds 100 lines -- assuming this is an error')
                if count_blank > 0:
                    storm_log.debug('Message line #%d: %s', i_line + 1, line)
            yield line
    msg = ''.join('%s\n' % line for line in read_message_lines())
    return json_decode(msg)

MODE = None
ANCHOR_TUPLE = None

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
    
def sync():
    sendMsgToParent({'command':'sync'})

def sendpid(heartbeatdir):
    pid = os.getpid()
    sendMsgToParent({'pid':pid})
    open(heartbeatdir + "/" + str(pid), "w").close()    

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

def ack(tup):
    """Acknowledge a tuple"""
    sendMsgToParent({"command": "ack", "id": tup.id})

def ackId(tupid):
    """Acknowledge a tuple when you only have its ID"""
    sendMsgToParent({"command": "ack", "id": tupid})

def fail(tup):
    """Fail a tuple"""
    sendMsgToParent({"command": "fail", "id": tup.id})

def reportError(msg):
    sendMsgToParent({"command": "error", "msg": msg})

def log(msg):
    sendMsgToParent({"command": "log", "msg": msg})

def initComponent():
    # Redirect stdout and stderr to logger instances. This is particularly
    # important for stdout so 'print' statements won't crash the Storm Java
    # worker.
    sys.stdout = LogStream(logging.getLogger('storm.stdout'))
    sys.stderr = LogStream(logging.getLogger('storm.stderr'))

    setupInfo = readMsg()
    storm_log.info('Task received setupInfo from Storm: %s', setupInfo)
    sendpid(setupInfo['pidDir'])
    storm_log.info('Task sent pid to Storm')
    return [setupInfo['conf'], setupInfo['context']]

class Tuple(object):
    __slots__ = ['id', 'component', 'stream', 'task', 'values']
    def __init__(self, id, component, stream, task, values):
        self.id = id
        self.component = component
        self.stream = stream
        self.task = task
        self.values = values

    def __eq__(self, other):
        if not isinstance(other, Tuple):
            return False
        
        for k in self.__slots__:
            if getattr(self, k) != getattr(other, k):
                return False
            
        return True

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '<%s%s>' % (
                self.__class__.__name__,
                ''.join(' %s=%r' % (k, getattr(self, k)) for k in sorted(self.__slots__)))

class Task(object):
    def shared_initialize(self):
        conf, context = initComponent()
        
        # These values are only available with a patched version of Storm.
        self.task_index = context.get('taskIndex', -1)
        self.worker_port = context.get('workerPort', -1)
        
        self.initialize(conf, context)

    def report_exception(self, base_message, exception):
        parameters = (
            base_message,
            os.environ.get('SCRIPT', sys.argv[0]),
            socket.gethostname(),
            'pid', os.getpid(),
            'port', self.worker_port,
            'taskindex', self.task_index,
            type(exception).__name__,
            #str(exception),
        )
        #message = '%s: %s (pid %d) on %s failed with %s: %s' % parameters
        message = '__'.join(str(p).replace('.', '_') for p in parameters)
        sendFailureMsgToParent(message)
        
        # Sleep for a few seconds to try and ensure Storm reads this message
        # before we terminate. If it does, then our message above will appear in
        # the Storm UI.
        time.sleep(5)

class Bolt(Task):
    def __init__(self):
        if TUPLE_PROFILING:
            self.profiler = BoltProfiler()
        else:
            self.profiler = None

    def initialize(self, stormconf, context):
        pass

    def process(self, tuple):
        pass

    def run(self):
        global MODE
        MODE = Bolt
        self.shared_initialize()
        profiler = self.profiler
        try:
            while True:
                if profiler is not None: profiler.pre_read()
                tup = readTuple()
                if profiler is not None: profiler.post_read()
                self.process(tup)
                if profiler is not None: profiler.post_process()
        except Exception, e:
            self.report_exception('E_BOLTFAILED', e)
            storm_log.exception('Caught exception in Bolt.run')
            if 'tup' in locals():
                # Only print the first 2000 characters of the tuple, otherwise
                # the message may be too long for certain handlers (e.g.
                # SysLogHandler).
                storm_log.error(
                    'The error occurred while processing this tuple: %s',
                    repr(tup.values)[:2000])

class BasicBolt(Task):
    def __init__(self):
        if TUPLE_PROFILING:
            self.profiler = BasicBoltProfiler()
        else:
            self.profiler = None

    def initialize(self, stormconf, context):
        pass

    def process(self, tuple):
        pass

    def run(self):
        global MODE
        MODE = Bolt
        global ANCHOR_TUPLE
        self.shared_initialize()
        profiler = self.profiler
        try:
            while True:
                if profiler is not None: profiler.pre_read()
                tup = readTuple()
                if profiler is not None: profiler.post_read()
                ANCHOR_TUPLE = tup
                self.process(tup)
                if profiler is not None: profiler.post_process()
                ack(tup)
                if profiler is not None: profiler.post_ack()
        except Exception, e:
            self.report_exception('E_BOLTFAILED', e)
            storm_log.exception('Caught exception in BasicBolt.run')
            if 'tup' in locals():
                # Only print the first 2000 characters of the tuple, otherwise
                # I've seen errors because the message is too long for
                # SysLogHandler.
                storm_log.error(
                    'The error occurred while processing this tuple: %s',
                    repr(tup.values)[:2000])

class Spout(Task):
    def initialize(self, conf, context):
        pass

    def ack(self, id):
        pass

    def fail(self, id):
        pass

    def nextTuple(self):
        pass

    def run(self):
        global MODE
        MODE = Spout
        self.shared_initialize()
        try:
            while True:
                msg = readCommand()
                command = msg["command"]
                if command == "next":
                    self.nextTuple()
                elif command == "ack":
                    self.ack(msg["id"])
                elif command == "fail":
                    self.fail(msg["id"])
                sync()
        except Exception, e:
            self.report_exception('E_SPOUTFAILED', e)
            storm_log.exception('Caught exception in Spout.run: %s', str(e))

class BoltProfiler(object):
    """Helper class for Bolt. Implements some simple log-based counters for
    profiling performance."""
    MAX_COUNT = 1000

    def __init__(self):
        self.read_time = self.process_time = 0.0
        self.num_tuples = self.total_num_tuples = 0
        self.start_interval = None

    def pre_read(self):
        self.t1 = time.time()
        if self.start_interval is None:
            self.start_interval = self.t1

    def post_read(self):
        self.t2 = time.time()
        self.read_time += self.t2 - self.t1

    def post_process(self):
        self.t3 = time.time()
        self.process_time += self.t3 - self.t2

        self.num_tuples += 1
        if self.num_tuples % self.MAX_COUNT == 0 or self.t3 - self.start_interval > 1.0:
            self.total_num_tuples += self.num_tuples
            self.total_time = self.read_time + self.process_time
            storm_log.debug(
                'Bolt profile: total_num_tuples=%d, num_tuples=%d, avg_read_time=%f (%.1f%%), avg_process_time=%f (%.1f%%)',
                self.total_num_tuples,
                self.num_tuples,
                self.read_time / self.num_tuples, self.read_time / self.total_time * 100.0,
                self.process_time / self.num_tuples, self.process_time / self.total_time * 100.0)

            # Clear the timing data.
            self.start_interval = None
            self.num_tuples = 0
            self.read_time = self.process_time = 0.0

class BasicBoltProfiler(object):
    """Helper class for BasicBolt. Implements some simple log-based counters for
    profiling performance."""
    MAX_COUNT = 1000

    def __init__(self):
        self.read_time = self.process_time = self.ack_time = 0.0
        self.num_tuples = self.total_num_tuples = 0
        self.start_interval = None

    def pre_read(self):
        self.t1 = time.time()
        if self.start_interval is None:
            self.start_interval = self.t1

    def post_read(self):
        self.t2 = time.time()
        self.read_time += self.t2 - self.t1

    def post_process(self):
        self.t3 = time.time()
        self.process_time += self.t3 - self.t2

    def post_ack(self):
        self.t4 = time.time()
        self.ack_time += self.t4 - self.t3

        self.num_tuples += 1
        if self.num_tuples % self.MAX_COUNT == 0 or self.t4 - self.start_interval > 1.0:
            self.total_num_tuples += self.num_tuples
            self.total_time = self.read_time + self.process_time + self.ack_time
            storm_log.debug(
                'BasicBolt profile: total_num_tuples=%d, num_tuples=%d, avg_read_time=%f (%.1f%%), avg_process_time=%f (%.1f%%), avg_ack_time=%f (%.1f%%)',
                self.total_num_tuples,
                self.num_tuples,
                self.read_time / self.num_tuples, self.read_time / self.total_time * 100.0,
                self.process_time / self.num_tuples, self.process_time / self.total_time * 100.0,
                self.ack_time / self.num_tuples, self.ack_time / self.total_time * 100.0)

            # Clear the timing data.
            self.start_interval = None
            self.num_tuples = 0
            self.read_time = self.process_time = self.ack_time = 0.0

def initialize_profiling():
    global TUPLE_PROFILING
    TUPLE_PROFILING = storm_log.isEnabledFor(logging.DEBUG)
    if TUPLE_PROFILING:
        storm_log.info('Tuple profiling enabled. Will log tuple processing times.')
    else:
        storm_log.info('Tuple profiling NOT enabled. Will not log tuple processing times.')

class LogStream(object):
    """Object that implements enough of the Python stream API to be used as
    sys.stdout and sys.stderr. Messages are written to the Python logger.
    """
    def __init__(self, logger):
        self.logger = logger
 
    def write(self, message):
        for line in message.split('\n'):
            self.logger.error(line)

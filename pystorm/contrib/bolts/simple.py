class SimpleBolt(Task):
    """A simplified bolt that automatically ACKs tuples

    This works exactly the same as `petrel.conponents.Bolt` except there's
    no need to call `self.ack()` at the end of `process`.

    """
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

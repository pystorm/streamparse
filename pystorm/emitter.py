import os
import sys

import storm

class EmitterBase(object):
    DEFAULT_PYTHON = 'python%d.%d' % (sys.version_info.major, sys.version_info.minor)

    def __init__(self, script):
        # We assume 'script' is in the current directory. We simply get the
        # base part and turn it into a .py name for inclusion in the Storm
        # jar we create.
        path, basename = os.path.split(os.path.relpath(script))
        assert len(path) == 0
        script = '%s.py' % os.path.splitext(basename)[0]
        self.execution_command = self.DEFAULT_PYTHON
        self.script = script
        self._json = {}
        super(EmitterBase, self).__init__()

    def declareOutputFields(declarer):
        raise NotImplementedError()

    def getComponentConfiguration(self):
        if len(self._json):
            return self._json
        else:
            return None

class Spout(EmitterBase, storm.Spout):
    pass

class BasicBolt(EmitterBase, storm.BasicBolt):
    pass

class Bolt(EmitterBase, storm.Bolt):
    pass

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os

here = os.path.split(os.path.abspath(__file__))[0]
root = os.path.abspath(os.path.join(here, '../../'))
sys.path[0:0] = [root]

from streamparse.bolt import BatchingBolt


class DummyBatchingBoltAutoAnchor(BatchingBolt):

    SECS_BETWEEN_BATCHES = 1
    AUTO_ANCHOR = True

    def group_key(self, tup):
        return tup.values[0]

    def process_batch(self, key, tups):
        self.emit([key, len(tups)])


if __name__ == '__main__':
    DummyBatchingBoltAutoAnchor().run()

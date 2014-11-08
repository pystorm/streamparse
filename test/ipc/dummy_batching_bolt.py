from __future__ import absolute_import, print_function, unicode_literals

import sys
import os

here = os.path.split(os.path.abspath(__file__))[0]
root = os.path.abspath(os.path.join(here, '../../'))
sys.path[0:0] = [root]

from streamparse.bolt import BatchingBolt


class DummyBatchingBolt(BatchingBolt):

    secs_between_batches = 1
    auto_ack = False
    auto_anchor = False
    auto_fail = False

    def group_key(self, tup):
        return tup.values[0]

    def process_batch(self, key, tups):
        for tup in tups:
            if tup.values[0] == "fail":
                raise Exception("Something bad happened!")
            self.emit([key, tup.id])


if __name__ == '__main__':
    DummyBatchingBolt().run()

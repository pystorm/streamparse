from __future__ import absolute_import, print_function, unicode_literals

import sys
import os

here = os.path.split(os.path.abspath(__file__))[0]
root = os.path.abspath(os.path.join(here, '../../'))
sys.path[0:0] = [root]

from streamparse.spout import Spout


class DummySpout(Spout):

    def next_tuple(self):
        self.emit(["test"])


if __name__ == '__main__':
    DummySpout().run()

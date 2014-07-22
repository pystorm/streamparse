from __future__ import absolute_import, print_function, unicode_literals

import sys
import os

here = os.path.split(os.path.abspath(__file__))[0]
root = os.path.abspath(os.path.join(here, '../../'))
sys.path[0:0] = [root]

from streamparse.bolt import BasicBolt


class DummyBolt(BasicBolt):

    def process(self, tup):
        if tup.id == "emit":
            self.emit(tup.values)


if __name__ == '__main__':
    DummyBolt().run()

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os

here = os.path.split(os.path.abspath(__file__))[0]
root = os.path.abspath(os.path.join(here, '../../'))
sys.path[0:0] = [root]

from streamparse.bolt import Bolt


class DummyBoltAutoFail(Bolt):

    auto_ack = False
    auto_anchor = False
    auto_fail = True

    def process(self, tup):
        raise Exception("Something bad happened!")


if __name__ == '__main__':
    DummyBoltAutoFail().run()

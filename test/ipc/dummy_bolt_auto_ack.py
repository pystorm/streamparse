from __future__ import absolute_import, print_function, unicode_literals

import sys
import os

here = os.path.split(os.path.abspath(__file__))[0]
root = os.path.abspath(os.path.join(here, '../../'))
sys.path[0:0] = [root]

from streamparse.bolt import Bolt


class DummyBoltAutoAck(Bolt):

    auto_ack = True
    auto_anchor = False
    auto_fail = False

    def process(self, tup):
        if tup.id == "emit_many":
            self.emit_many([tup.values] * 5)
        else:
            self.emit(tup.values)


if __name__ == '__main__':
    DummyBoltAutoAck().run()

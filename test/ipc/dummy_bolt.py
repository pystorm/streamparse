from __future__ import absolute_import, print_function, unicode_literals

import sys
import os

here = os.path.split(os.path.abspath(__file__))[0]
root = os.path.abspath(os.path.join(here, '../../'))
sys.path[0:0] = [root]

from streamparse.bolt import Bolt


class DummyBolt(Bolt):

    def process(self, tup):
        if tup.id != "emit_many":
            self.emit(tup.values)

        if tup.id == "ack_me":
            self.ack(tup)
        elif tup.id == "fail_me":
            self.fail(tup)
        elif tup.id == "emit_many":
            self.emit_many([tup.values]*5)


if __name__ == '__main__':
    DummyBolt().run()

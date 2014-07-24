from __future__ import absolute_import, print_function, unicode_literals

import sys
import os

here = os.path.split(os.path.abspath(__file__))[0]
root = os.path.abspath(os.path.join(here, '../../'))
sys.path[0:0] = [root]

from streamparse.bolt import Bolt


class DummyBolt(Bolt):

    auto_ack = False
    auto_anchor = False
    auto_fail = False

    def process(self, tup):
        if tup.id == "ack_me":
            self.emit(tup.values)
            self.ack(tup)
        elif tup.id == "fail_me":
            self.fail(tup)
        elif tup.id == "anchor|1,2,3":
            self.emit(tup.values, anchors=["1", "2", "3"])
        elif tup.id == "stream-words":
            self.emit(tup.values, stream="words")
        elif tup.id == "direct_task|12":
            self.emit(tup.values, direct_task=12)
        elif tup.id == "exception":
            raise Exception("Something bad happened!")
        elif tup.id == "emit_many":
            self.emit_many([tup.values]*5)
        else:
            self.emit(tup.values)


if __name__ == '__main__':
    DummyBolt().run()

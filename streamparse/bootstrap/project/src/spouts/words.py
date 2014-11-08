from __future__ import absolute_import, print_function, unicode_literals

import itertools
from streamparse.spout import Spout

class WordSpout(Spout):

    def initialize(self, stormconf, context):
        self.words = itertools.cycle(['dog', 'cat',
                                      'zebra', 'elephant'])

    def next_tuple(self):
        word = next(self.words)
        self.emit([word])

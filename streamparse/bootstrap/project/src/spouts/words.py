from itertools import cycle

from streamparse import Spout


class WordSpout(Spout):
    outputs = ['word']

    def initialize(self, stormconf, context):
        self.words = cycle(['dog', 'cat', 'zebra', 'elephant'])

    def next_tuple(self):
        word = next(self.words)
        self.emit([word])

from itertools import cycle
from collections import Counter

from streamparse.spout import Spout
from streamparse.bolt import Bolt


class WordSpout(Spout):
    def initialize(self, stormconf, context):
        self.words = cycle(['dog', 'cat',
                            'zebra', 'elephant'])

    def next_tuple(self):
        word = next(self.words)
        self.emit([word])


class WordCountBolt(Bolt):
    def initialize(self, conf, ctx):
        self.counter = Counter()

    def process(self, tup):
        word, = tup.values
        self.log_count(word)

    def log_count(self, word):
        ct = self.counter
        ct[word] += 1;
        ct["total"] += 1

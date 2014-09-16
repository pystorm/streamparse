from redis import StrictRedis
from itertools import cycle
from collections import Counter
import os

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
        self.redis = StrictRedis()
        self.counter = Counter()
        self.pid = os.getpid()

    def process(self, tup):
        word, = tup.values
        inc_by = 10 if word == "dog" else 1
        self.redis.zincrby("words", word, inc_by)
        self.log_count(word)

    def log_count(self, word):
        ct = self.counter
        ct[word] += 1; ct["total"] += 1
        total = ct["total"]
        if total % 1000 == 0:
            self.log("counted [{:,}] words [pid={}]"
                     .format(total, self.pid))

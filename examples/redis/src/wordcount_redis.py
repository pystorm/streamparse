import os
from collections import Counter
from itertools import cycle

from redis import StrictRedis

from streamparse.bolt import Bolt
from streamparse.spout import Spout


class WordSpout(Spout):
    outputs = ['word']

    def initialize(self, stormconf, context):
        self.words = cycle(['dog', 'cat', 'zebra', 'elephant'])

    def next_tuple(self):
        word = next(self.words)
        self.emit([word])


class WordCountBolt(Bolt):
    outputs = ['word', 'count']

    def initialize(self, conf, ctx):
        self.redis = StrictRedis()
        self.counter = Counter()
        self.pid = os.getpid()

    def process(self, tup):
        word, = tup.values
        inc_by = 10 if word == "dog" else 1
        self.redis.zincrby("words", word, inc_by)
        self.log_count(word)
        self.emit([word, self.counter[word]])

    def log_count(self, word):
        self.counter[word] += 1
        total = len(self.counter)
        if total % 1000 == 0:
            self.logger.info("counted [{:,}] words [pid={}]".format(total,
                                                                    self.pid))

import os
from collections import Counter

from redis import StrictRedis

from streamparse import Bolt


class WordCountBolt(Bolt):
    outputs = ['word', 'count']

    def initialize(self, conf, ctx):
        self.counter = Counter()
        self.pid = os.getpid()
        self.total = 0

    def _increment(self, word, inc_by):
        self.counter[word] += inc_by
        self.total += inc_by

    def process(self, tup):
        word = tup.values[0]
        self._increment(word, 10 if word == "dog" else 1)
        if self.total % 1000 == 0:
            self.logger.info("counted [{:,}] words [pid={}]".format(self.total,
                                                                    self.pid))
        self.emit([word, self.counter[word]])


class RedisWordCountBolt(WordCountBolt):
    def initialize(self, conf, ctx):
        self.pid = os.getpid()
        self.redis = StrictRedis()
        self.total = 0

    def _increment(self, word, inc_by):
        self.total += inc_by
        self.redis.zincrby("words", word, inc_by)

from __future__ import absolute_import, print_function, unicode_literals

from collections import Counter
from streamparse.bolt import Bolt


class WordCounter(Bolt):

    auto_ack = True  # automatically acknowledge tuples after process()
    auto_anchor = True  # automatically anchor tuples to current tuple
    auto_fail = True  # automatically fail tuples when exceptions occur

    def initialize(self, conf, ctx):
        self.counts = Counter()

    def process(self, tup):
        word = tup.values[0]
        self.counts[word] += 1
        self.emit([word, self.counts[word]])
        self.log('%s: %d' % (word, self.counts[word]))

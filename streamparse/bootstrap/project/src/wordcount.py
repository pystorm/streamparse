from collections import Counter

from streamparse import storm

class WordCounter(storm.Bolt):

    def initialize(self, conf, ctx):
        self.counts = Counter()

    def process(self, tup):
        word = tup.values[0]
        self.counts[word] += 1
        storm.emit([word, self.counts[word]])
        storm.log('%s: %d' % (word, self.counts[word]))

WordCounter().run()

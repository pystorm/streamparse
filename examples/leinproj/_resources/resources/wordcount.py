from collections import defaultdict
from pystorm import storm
from pystorm.storm import BasicBolt

class WordCounter(BasicBolt):

    def initialize(self, stormconf, context):
        self.counts = defaultdict(int)

    def process(self, tup):
        word = tup.values[0]
        self.counts[word] += 1
        if self.counts[word] % 10 == 0:
            storm.emit([word, self.counts[word]])
            storm.log('%s: %d' % (word, self.counts[word]))

WordCounter().run()

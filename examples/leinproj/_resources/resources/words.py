import itertools

from pystorm import storm
from pystorm.storm import Spout

class WordSpout(Spout):

    def reader(self):
        with open('./pg12.txt') as f:
            for line in f.readlines():
                words = line.lower().strip().split()
                for word in words:
                    if word:
                        yield word

    def initialize(self, stormconf, context):
        #self.words = reader()
        self.words = itertools.cycle(['a', 'b', 'c', 'd'])

    def nextTuple(self):
        word = next(self.words)
        storm.emit([word,])

WordSpout().run()

import itertools

from streamparse import storm

class WordSpout(storm.Spout):

    def initialize(self, stormconf, context):
        self.words = itertools.cycle(['dog', 'cat',
                                      'zebra', 'elephant'])

    def nextTuple(self):
        word = next(self.words)
        storm.emit([word])


if __name__ == '__main__':
    WordSpout().run()

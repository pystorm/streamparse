import itertools

from streamparse.spout import Spout

class WordSpout(Spout):

    def initialize(self, stormconf, context):
        self.words = itertools.cycle(['dog', 'cat',
                                      'zebra', 'elephant'])

    def next_tuple(self):
        word = next(self.words)
        self.emit([word])


if __name__ == '__main__':
    WordSpout().run()

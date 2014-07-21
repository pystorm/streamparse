import datetime as dt
from collections import Counter

from streamparse.bolt import BatchingBolt


class PixelCounter(BatchingBolt):

    def initialize(self, conf, ctx):
        self.counts = Counter()

    def group_key(self, tup):
        hour = tup.values[0]
        return hour

    def process_batch(self, key, tups):
        self.emit([key, len(tups)])


if __name__ == '__main__':
    PixelCounter().run()

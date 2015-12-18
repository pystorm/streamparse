from collections import Counter

from streamparse.bolt import BatchingBolt


class PixelCounterBolt(BatchingBolt):
    outputs = []

    def initialize(self, conf, ctx):
        self.counts = Counter()

    def group_key(self, tup):
        url = tup.values[2]
        return url

    def process_batch(self, key, tups):
        self.counts[key] += len(tups)
        self.emit([key, self.counts[key]])

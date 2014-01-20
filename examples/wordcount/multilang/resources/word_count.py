from collections import defaultdict

from pystorm.bolt import BasicBolt


class WordCountBolt(BasicBolt):

    word_count = defaultdict(int)

    def process(self, tup):
        for word in tup.values:
            self.word_count[word] += 1
            BasicBolt.emit([word, self.word_count[word]])


if __name__ == '__main__':
    WordCountBolt().run()
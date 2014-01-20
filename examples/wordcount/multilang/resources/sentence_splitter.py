from pystorm.bolt import BasicBolt


class SentenceSplitterBolt(BasicBolt):

    def process(self, tup):
        sentence = tup.values[0]
        for word in sentence.split(' '):
            BasicBolt.emit(word)


if __name__ == '__main__':
    SentenceSplitterBolt().run()

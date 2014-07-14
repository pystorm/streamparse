import random

from streamparse.spout import Spout


class SentenceSpout(Spout):

    sentences = (
        "a little brown dog",
        "the man petted the dog",
        "four score and seven years ago",
        "an apple a day keeps the doctor away",
    )

    def next_tuple(self):
        self.emit([random.choice(self.sentences)])


if __name__ == '__main__':
    SentenceSpout().run()

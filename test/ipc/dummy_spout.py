from streamparse.spout import Spout


class DummySpout(Spout):

    def next_tuple(self):
        self.emit(["test"])


if __name__ == '__main__':
    DummySpout().run()

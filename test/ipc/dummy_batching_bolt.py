from streamparse.bolt import BatchingBolt


class DummyBatchingBolt(BatchingBolt):

    def group_key(self, tup):
        return tup.values[0]

    def process_batch(self, key, tups):
        for tup in tups:
            if tup.values[0] == "fail":
                raise Exception("Something bad happened!")
            self.emit([key, tup.id])


if __name__ == '__main__':
    DummyBatchingBolt().run()

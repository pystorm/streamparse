from streamparse.bolt import Bolt


class DummyBolt(Bolt):

    def process(self, tup):
        if tup.id != "emit_many":
            self.emit(tup.values)

        if tup.id == "ack_me":
            self.ack(tup)
        elif tup.id == "fail_me":
            self.fail(tup)
        elif tup.id == "emit_many":
            self.emit_many([tup.values]*5)


if __name__ == '__main__':
    DummyBolt().run()

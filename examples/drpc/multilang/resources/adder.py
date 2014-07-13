import re

from streamparse.bolt import BasicBolt


class AdderBolt(BasicBolt):

    def process(self, tup):
        request_id, args = tup.values

        args = re.sub(r' {2,}', ' ', args)
        args = [int(x) for x in args.split(' ')]
        total = args[0]

        for arg in args[1:]:
            total += arg

        BasicBolt.emit([request_id, total])


if __name__ == '__main__':
    AdderBolt().run()

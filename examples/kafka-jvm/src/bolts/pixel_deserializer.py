import simplejson as json
from streamparse.bolt import Bolt


class PixelDeserializerBolt(Bolt):
    outputs = ["ip", "ts", "url"]

    def process(self, tup):
        # Exceptions are automatically caught and reported
        msg = json.loads(tup.values[0])
        ip = msg.get("ip")
        ts = msg.get("ts")
        url = msg.get("url")
        self.emit([ip, ts, url])  # auto anchored

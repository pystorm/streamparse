import logging

import simplejson as json
from streamparse.storm import Bolt


class PixelDeserializerBolt(Bolt):

    def process(self, tup):
        # Exceptions are automatically caught and reported
        msg = json.loads(tup.values[0])
        ip = msg.get("ip")
        ts = msg.get("ts")
        url = msg.get("url")
        self.emit([ip, ts, url]) # auto anchored

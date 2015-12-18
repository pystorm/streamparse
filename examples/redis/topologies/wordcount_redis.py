"""
Word count topology (in Redis)
"""

from streamparse import Topology

from bolts import RedisWordCountBolt
from spouts import WordSpout


class WordCount(Topology):
    word_spout = WordSpout.spec()
    count_bolt = RedisWordCountBolt.spec(inputs=[word_spout], par=4)

"""
Word count topology (in Redis)
"""

from src.bolts import RedisWordCountBolt
from src.spouts import WordSpout
from streamparse import Topology


class WordCount(Topology):
    word_spout = WordSpout.spec()
    count_bolt = RedisWordCountBolt.spec(inputs=[word_spout], par=4)

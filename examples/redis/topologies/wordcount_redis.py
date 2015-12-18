"""
Word count topology (in Redis)
"""

from streamparse import Grouping, Topology

from wordcount_redis import WordCountBolt, WordSpout


class WordCount(Topology):
    word_spout = WordSpout.spec()
    count_bolt = WordCountBolt.spec(inputs=[word_spout], par=4)

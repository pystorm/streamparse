"""
Word count topology (in memory)
"""

from streamparse import Grouping, Topology

from wordcount_mem import WordCountBolt, WordSpout


class WordCount(Topology):
    word_spout = WordSpout.spec()
    count_bolt = WordCountBolt.spec(inputs={word_spout: Grouping.fields('word')},
                                    par=2)

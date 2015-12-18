"""
Word count topology (in memory)
"""

from streamparse import Grouping, Topology

from bolts import WordCountBolt
from spouts import WordSpout


class WordCount(Topology):
    word_spout = WordSpout.spec()
    count_bolt = WordCountBolt.spec(inputs={word_spout: Grouping.fields('word')},
                                    par=2)

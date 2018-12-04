"""
Word count topology (in memory)
"""

from src.bolts import WordCountBolt
from src.spouts import WordSpout
from streamparse import Grouping, Topology


class WordCount(Topology):
    word_spout = WordSpout.spec()
    count_bolt = WordCountBolt.spec(inputs={word_spout: Grouping.fields("word")}, par=2)

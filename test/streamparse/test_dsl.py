"""
Tests for Topology DSL
"""

import logging
import unittest

from streamparse.dsl import Grouping, Topology
from streamparse.storm import (Bolt, Component, JavaBolt, JavaSpout, ShellBolt,
                               ShellSpout, Spout)


log = logging.getLogger(__name__)


class WordSpout(Spout):
    outputs = ["word"]


class WordCountBolt(Bolt):
    outputs = ["word", "count"]


class TopologyTests(unittest.TestCase):
    def test_basic_spec(self):
        class WordCount(Topology):
            word_spout = WordSpout.spec(par=2)
            word_bolt = WordCountBolt.spec(inputs={word_spout:
                                                   Grouping.fields("word")},
                                           par=8)

        self.assertEqual(len(WordCount.specs), 2)
        self.assertEqual(list(WordCount.word_bolt.inputs.keys())[0],
                         WordCount.word_spout['default'])
        self.assertEqual(WordCount.word_bolt.inputs[WordCount.word_spout['default']],
                         Grouping.fields('word'))

    def test_invalid_spout_source(self):
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = WordSpout.spec(source='unknown')

    def test_invalid_bolt_source(self):
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_bolt = WordCountBolt.spec()

    def test_invalid_par(self):
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = WordSpout.spec(par=0)

    def test_invalid_bolt_group_field(self):
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs={word_spout:
                                                       Grouping.fields("foo")})

    def test_empty_bolt_group_field(self):
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs={word_spout:
                                                       Grouping.fields()})

    def test_duplicate_name(self):
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word = WordSpout.spec()
                word_ = WordCountBolt.spec(name='word', inputs=[word])

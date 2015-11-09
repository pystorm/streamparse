import unittest
import logging

from streamparse.dsl.exceptions import TopologyError
from streamparse.dsl.stream import Grouping
from streamparse.dsl.topology import Topology
from streamparse.storm.bolt import Bolt
from streamparse.storm.spout import Spout


log = logging.getLogger(__name__)


class WordSpout(Spout):
    outputs = ["word"]


class WordCountBolt(Bolt):
    outputs = ["word", "count"]


class TopologyTests(unittest.TestCase):
    def test_basic_spec(self):
        class WordCount(Topology):
            word_spout = WordSpout.spec(parallelism=2)
            word_bolt = WordCountBolt.spec(inputs={word_spout:
                                                   Grouping.fields("word")},
                                           parallelism=8)

        self.assertEqual(len(WordCount.specs), 2)
        self.assertEqual(list(WordCount.word_bolt.inputs.keys())[0],
                         WordCount.word_spout['default'])
        self.assertEqual(WordCount.word_bolt[WordCount.word_spout['default']],
                         Grouping.fields('word'))

    def test_bolt_before_source(self):
        class WordCount(Topology):
            word_spout = WordSpout.spec()
            word_bolt = WordCountBolt.spec(inputs=word_spout)
        self.assertEqual(WordCount.word_bolt.inputs[0], WordCount.word_spout)

    def test_invalid_spout_source(self):
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = WordSpout.spec(source='unknown')

    def test_invalid_bolt_source(self):
        with self.assertRaises(TopologyError):
            class WordCount(Topology):
                word_bolt = WordCountBolt.spec()

    def test_invalid_parallelism(self):
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = WordSpout.spec(parallelism=0)

    def test_invalid_bolt_group_on(self):
        with self.assertRaises(TopologyError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs={word_spout:
                                                       Grouping.fields("foo")})

    def test_duplicate_name(self):
        with self.assertRaises(TopologyError):
            class WordCount(Topology):
                word = WordSpout.spec()
                word_ = WordCountBolt.spec(name='word', inputs=[word])

import unittest
import logging
from streamparse.dsl.topology import Topology, Grouping, TopologyError
from streamparse.dsl.spec import Spec
from streamparse.storm.spout import Spout
from streamparse.storm.bolt import Bolt

log = logging.getLogger(__name__)


class WordSpout(Spout):
    streams = ["word"]


class WordCountBolt(Bolt):
    streams = ["word", "count"]


class TopologyTests(unittest.TestCase):
    def test_basic_spec(self):
        class WordCount(Topology):
            word_spout = Spec(
                WordSpout,
                parallelism=2,
            )
            word_bolt = Spec(
                WordCountBolt,
                source=word_spout,
                group_on=Grouping.fields("word"),
                parallelism=8,
            )

        self.assertEqual(len(WordCount.specs), 2)
        self.assertEqual(WordCount.word_bolt.sources[0], WordCount.word_spout)
        self.assertEqual(WordCount.word_bolt.group_on, ['word'])

    def test_bolt_before_source(self):
        class WordCount(Topology):
            word_bolt = Spec(
                WordCountBolt,
                source='word_spout',
            )
            word_spout = Spec(WordSpout)

        self.assertEqual(WordCount.word_bolt.sources[0], WordCount.word_spout)

    def test_invalid_spout_source(self):
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = Spec(
                    WordSpout,
                    source='unknown',
                )

    def test_invalid_bolt_source(self):
        with self.assertRaises(TopologyError):
            class WordCount(Topology):
                word_bolt = Spec(
                    WordCountBolt,
                )

    def test_invalid_parallelism(self):
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = Spec(
                    WordSpout,
                    parallelism=0,
                )

    def test_invalid_bolt_group_on(self):
        with self.assertRaises(TopologyError):
            class WordCount(Topology):
                word_spout = Spec(
                    WordSpout,
                )
                word_bolt = Spec(
                    WordCountBolt,
                    source=word_spout,
                    group_on=Grouping.fields("foo"),
                )

    def test_duplicate_name(self):
        with self.assertRaises(TopologyError):
            class WordCount(Topology):
                word = Spec(
                    WordSpout,
                )
                word_ = Spec(
                    WordCountBolt,
                    name='word',
                    source=word,
                )

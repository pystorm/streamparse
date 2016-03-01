"""
Tests for Topology DSL
"""

import logging
import unittest
from io import BytesIO

from streamparse.dsl import Grouping, Stream, Topology
from streamparse.storm import (Bolt, Component, JavaBolt, JavaSpout, ShellBolt,
                               ShellSpout, Spout)


log = logging.getLogger(__name__)


class WordSpout(Spout):
    outputs = ["word"]


class WordCountBolt(Bolt):
    outputs = ["word", "count"]


class MultiStreamWordCountBolt(Bolt):
    outputs = [Stream(fields=['word', 'count']),
               Stream(fields=['all_word_count'], name='sum')]


class DatabaseDumperBolt(Bolt):
    outputs = []


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
        self.assertEqual(WordCount.thrift_spouts['word_spout'].common.parallelism_hint,
                         2)
        self.assertEqual(WordCount.thrift_bolts['word_bolt'].common.parallelism_hint,
                         8)
        self.assertEqual(WordCount.word_bolt.inputs[WordCount.word_spout['default']],
                         Grouping.fields('word'))

    def test_spec_with_inputs_as_list(self):
        class WordCount(Topology):
            word_spout = WordSpout.spec(par=2)
            word_bolt = WordCountBolt.spec(inputs=[word_spout], par=8)
        self.assertEqual(len(WordCount.specs), 2)
        self.assertEqual(len(WordCount.thrift_spouts), 1)
        self.assertEqual(len(WordCount.thrift_bolts), 1)
        self.assertEqual(list(WordCount.word_bolt.inputs.keys()),
                         [WordCount.word_spout['default']])
        self.assertEqual(WordCount.word_bolt.inputs[WordCount.word_spout['default']],
                         Grouping.SHUFFLE)

    def test_multi_stream_bolt(self):
        class WordCount(Topology):
            word_spout = WordSpout.spec(par=2)
            word_bolt = MultiStreamWordCountBolt.spec(inputs=[word_spout],
                                                      par=8)
            db_dumper_bolt = DatabaseDumperBolt.spec(par=4,
                                                     inputs=[word_bolt['sum'],
                                                             word_bolt['default']])
        self.assertEqual(len(WordCount.specs), 3)
        self.assertEqual(len(WordCount.thrift_spouts), 1)
        self.assertEqual(len(WordCount.thrift_bolts), 2)
        self.assertEqual(list(WordCount.word_bolt.inputs.keys()),
                         [WordCount.word_spout['default']])
        self.assertEqual(WordCount.word_bolt.inputs[WordCount.word_spout['default']],
                         Grouping.SHUFFLE)
        db_dumper_bolt_input_set = set(WordCount.db_dumper_bolt.inputs.keys())
        self.assertEqual(len(WordCount.db_dumper_bolt.inputs.keys()),
                         len(db_dumper_bolt_input_set))
        self.assertEqual(db_dumper_bolt_input_set,
                         {WordCount.word_bolt['sum'], WordCount.word_bolt['default']})

    def test_long_chain_spec(self):
        class WordCount(Topology):
            word_spout = WordSpout.spec()
            word_bolt1 = WordCountBolt.spec(inputs=[word_spout])
            word_bolt2 = WordCountBolt.spec(inputs=[word_bolt1])
            word_bolt3 = WordCountBolt.spec(inputs=[word_bolt2])
            word_bolt4 = WordCountBolt.spec(inputs=[word_bolt3])
            word_bolt5 = WordCountBolt.spec(inputs=[word_bolt4])
            word_bolt6 = WordCountBolt.spec(inputs=[word_bolt5])
            word_bolt7 = WordCountBolt.spec(inputs=[word_bolt6])
            word_bolt8 = WordCountBolt.spec(inputs=[word_bolt7])
            word_bolt9 = WordCountBolt.spec(inputs=[word_bolt8])
            word_bolt10 = WordCountBolt.spec(inputs=[word_bolt9])
            word_bolt11 = WordCountBolt.spec(inputs=[word_bolt10])
            word_bolt12 = WordCountBolt.spec(inputs=[word_bolt11])
        self.assertEqual(len(WordCount.specs), 13)
        self.assertEqual(len(WordCount.thrift_spouts), 1)
        self.assertEqual(len(WordCount.thrift_bolts), 12)
        self.assertEqual(list(WordCount.word_bolt1.inputs.keys())[0],
                         WordCount.word_spout['default'])
        self.assertEqual(WordCount.word_bolt1.inputs[WordCount.word_spout['default']],
                         Grouping.SHUFFLE)
        for i in range(2, 13):
            bolt = getattr(WordCount, 'word_bolt{}'.format(i))
            prev_bolt = getattr(WordCount, 'word_bolt{}'.format(i - 1))
            self.assertEqual(list(bolt.inputs.keys())[0], prev_bolt['default'])
            self.assertEqual(bolt.inputs[prev_bolt['default']], Grouping.SHUFFLE)

    def test_many_spouts_spec(self):
        class WordCount(Topology):
            word_spout1 = WordSpout.spec()
            word_spout2 = WordSpout.spec()
            word_spout3 = WordSpout.spec()
            word_spout4 = WordSpout.spec()
            word_spout5 = WordSpout.spec()
            word_bolt = WordCountBolt.spec(inputs=[word_spout1, word_spout2,
                                                   word_spout3, word_spout4,
                                                   word_spout5])

    def test_invalid_bolt_group_field(self):
        # Fields grouping must specify field output by spout
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs={word_spout:
                                                       Grouping.fields("foo")})

    def test_empty_bolt_group_field(self):
        # Fields groupings require field names to be specified
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs={word_spout:
                                                       Grouping.fields()})

    def test_duplicate_name(self):
        # Each component name must be unique
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word = WordSpout.spec()
                word_ = WordCountBolt.spec(name='word', inputs=[word])

    def test_no_input_bolt(self):
        # All bolts must have at least one input
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs=[])

    def test_no_outputs_spout_empty(self):
        # All spouts must have output fields
        class PointlessSpout(Spout):
            outputs = []
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = PointlessSpout.spec()

    def test_no_outputs_spout(self):
        # All spouts must have output fields
        class PointlessSpout(Spout):
            outputs = []
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = PointlessSpout.spec()

    def test_base_component_rejection(self):
        # Topology components must inherit from Bolt/Spout, not Component directly
        class MyComponent(Component):
            outputs = []
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = MyComponent.spec()

    def test_component_instead_of_spec(self):
        # Make sure we catch things early when people forget to call .spec
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = WordSpout(input_stream=BytesIO(),
                                       output_stream=BytesIO())

    def test_no_spout(self):
        # Every topology must have a spout
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                pass

    def test_zero_par(self):
        # Component parallelism (number of processes) can't be 0
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = WordSpout.spec(par=0)

    def test_negative_par(self):
        # Component parallelism (number of processes) can't be negative
        with self.assertRaises(ValueError):
            class WordCount(Topology):
                word_spout = WordSpout.spec(par=-1)

    def test_float_par(self):
        # Component parallelism (number of processes) must be an int
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = WordSpout.spec(par=5.4)

    def test_invalid_bolt_input_dict_key(self):
        # Keys in input dict must be either GlobalStreamId or ComponentSpec
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs={'word_spout':
                                                       Grouping.fields('word')})

    def test_invalid_bolt_input_dict_val(self):
        # Values in input dict must be Grouping objects
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs={word_spout:
                                                       'word'})

    def test_invalid_bolt_input_str(self):
        # inputs must be either list, dict, or None; not str
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs='word_spout')

    def test_invalid_config_str(self):
        # configs must be either dict, or None; not str
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(config='{"foo": "bar"}')

    def test_invalid_outputs_entry_int(self):
        # Outputs must either be list of strings or list of streams, not ints
        class BadSpout(Spout):
            outputs = ['foo', 2]
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                bad_spout = BadSpout.spec()
                word_bolt = WordCountBolt.spec(inputs=[bad_spout])

    def test_invalid_outputs_str(self):
        # Outputs must either be list of strings or list of streams
        class BadSpout(Spout):
            outputs = 'foo'
        with self.assertRaises(TypeError):
            class WordCount(Topology):
                bad_spout = BadSpout.spec()
                word_bolt = WordCountBolt.spec(inputs=[bad_spout])

    def test_unknown_stream(self):
        # Should raise keyerror if stream name is not valid
        with self.assertRaises(KeyError):
            class WordCount(Topology):
                word_spout = WordSpout.spec()
                word_bolt = WordCountBolt.spec(inputs=[word_spout['word']])

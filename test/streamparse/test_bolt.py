from __future__ import absolute_import, print_function, unicode_literals

import itertools
import mock
import time
import unittest

from mock import patch

from streamparse import bolt, ipc

class BoltTests(unittest.TestCase):

    def setUp(self):
        self.bolt = bolt.Bolt()
        self.bolt.initialize({}, {})

    @patch('streamparse.bolt.send_message')
    def test_emit(self, send_message_mock):
        # A basic emit
        self.bolt.emit([1, 2, 3])
        send_message_mock.assert_called_with(
            {u'command': u'emit', u'anchors': [], u'tuple': [1, 2, 3]}
        )

        # Emit with stream and anchors
        self.bolt.emit([1, 2, 3], stream='foo', anchors=[4, 5])
        send_message_mock.assert_called_with(
            {u'command': u'emit',
             u'stream': 'foo',
             u'anchors': [4, 5],
             u'tuple': [1, 2, 3]}
        )

        # Emit as a direct task
        self.bolt.emit([1, 2, 3], direct_task='other_bolt')
        send_message_mock.assert_called_with(
            {u'command': u'emit',
             u'anchors': [],
             u'tuple': [1, 2, 3],
             u'task': 'other_bolt'}
        )

    @patch('streamparse.bolt.send_message')
    def test_emit_many(self, send_message_mock):
        # emit_many will be tested once issue #44 is resolved
        # until then, it's a pain and not worth dealing with
        pass


    @patch('streamparse.bolt.send_message')
    def test_ack(self, send_message_mock):
        # ack an ID
        self.bolt.ack(42)
        send_message_mock.assert_called_with(
            {'command': 'ack', 'id': 42}
        )

        # ack a Tuple
        tup = ipc.Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        self.bolt.ack(tup)
        send_message_mock.assert_called_with(
            {'command': 'ack', 'id': 14}
        )

    @patch('streamparse.bolt.send_message')
    def test_fail(self, send_message_mock):
        # fail an ID
        self.bolt.fail(42)
        send_message_mock.assert_called_with(
            {'command': 'fail', 'id': 42}
        )

        # fail a Tuple
        tup = ipc.Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        self.bolt.ack(tup)
        send_message_mock.assert_called_with(
            {'command': 'ack', 'id': 14}
        )

    @patch.object(bolt.Bolt, 'process')
    @patch.object(bolt.Bolt, 'ack')
    @patch('streamparse.bolt.read_tuple')
    def test_run(self, read_tuple_mock, ack_mock, process_mock):
        tup = ipc.Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        read_tuple_mock.return_value = tup
        self.bolt._run()
        process_mock.assert_called_with(tup)
        self.assertListEqual(self.bolt._current_tups, [])

    @patch.object(bolt.Bolt, 'process')
    @patch.object(bolt.Bolt, 'ack')
    @patch('streamparse.bolt.read_tuple')
    def test_auto_ack(self, read_tuple_mock, ack_mock, process_mock):
        tup = ipc.Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        read_tuple_mock.return_value = tup

        # test auto-ack on (the default)
        self.bolt._run()
        ack_mock.assert_called_with(tup)
        ack_mock.reset_mock()

        # test auto-ack off
        self.bolt.auto_ack = False
        self.bolt._run()
        self.assertFalse(ack_mock.called)

    @patch('streamparse.bolt.send_message')
    def test_auto_anchor(self, send_message_mock):
        tup = ipc.Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        self.bolt._current_tups = [tup]

        # Test auto-anchor on (the default)
        self.bolt.emit([1, 2, 3])
        send_message_mock.assert_called_with(
            {u'command': u'emit', u'anchors': [14], u'tuple': [1, 2, 3]}
        )

        # Test auto-anchor off
        self.bolt.auto_anchor = False
        self.bolt.emit([1, 2, 3])
        send_message_mock.assert_called_with(
            {u'command': u'emit', u'anchors': [], u'tuple': [1, 2, 3]}
        )

        # Test overriding auto-anchor
        self.bolt.auto_anchor = True
        self.bolt.emit([1, 2, 3], anchors=[42])
        send_message_mock.assert_called_with(
            {u'command': u'emit', u'anchors': [42], u'tuple': [1, 2, 3]}
        )

    @patch('sys.exit', new=lambda r: r)
    @patch('streamparse.bolt.read_handshake', new=lambda: (None, None))
    @patch.object(bolt.Bolt, 'raise_exception', new=lambda *a: None)
    @patch.object(bolt.Bolt, 'fail')
    @patch.object(bolt.Bolt, '_run')
    def test_auto_fail(self, _run_mock, fail_mock):
        tup = ipc.Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        self.bolt._current_tups = [tup]
        # Make sure _run raises an exception
        def raiser(): # lambdas can't raise
            raise Exception('borkt')
        _run_mock.side_effect = raiser

        # test auto-fail on (the default)
        self.bolt.run()
        fail_mock.assert_called_with(tup)
        fail_mock.reset_mock()

        # test auto-fail off
        self.bolt.auto_fail = False
        self.bolt.run()
        self.assertFalse(fail_mock.called)


@patch('streamparse.bolt.send_message', new=lambda t: None)
class BatchingBoltTests(unittest.TestCase):

    class ShortBatchTester(bolt.BatchingBolt):
        secs_between_batches = 0.05 # keep it speedy

    def setUp(self):
        self.bolt = self.ShortBatchTester()
        self.bolt.initialize({}, {})
        self.tups = [
            ipc.Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3]),
            ipc.Tuple(15, 'some_spout', 'default', 'some_bolt', [4, 5, 6]),
            ipc.Tuple(16, 'some_spout', 'default', 'some_bolt', [7, 8, 9]),
        ]
        self.tups_cycle = itertools.cycle(self.tups)

    @patch.object(bolt.BatchingBolt, 'process_batch')
    @patch('streamparse.bolt.read_tuple')
    def test_batching(self, read_tuple_mock, process_batch_mock):
        # Basic test that batching is working
        read_tuple_mock.side_effect = lambda: self.tups_cycle.next()

        # Add a bunch of tuples
        for i in xrange(3):
            self.bolt._run()

        # Wait a bit, and see if process_batch was called
        time.sleep(0.1)
        process_batch_mock.assert_called_with(None, self.tups[:3])

    @patch.object(bolt.BatchingBolt, 'process_batch')
    @patch('streamparse.bolt.read_tuple')
    def test_group_key(self, read_tuple_mock, process_batch_mock):
        # Basic test that batching is working
        read_tuple_mock.side_effect = lambda: self.tups_cycle.next()

        # Change the group key
        self.bolt.group_key = lambda t: sum(t.values) % 2

        # Add a bunch of tuples
        for i in xrange(3):
            self.bolt._run()

        # Wait a bit, and see if process_batch was called correctly
        time.sleep(0.1)
        process_batch_mock.assert_has_calls([
            mock.call(0, [self.tups[0], self.tups[2]]),
            mock.call(1, [self.tups[1]]),
        ], any_order=True)

    def test_auto_ack(self):
        pass

    def test_auto_anchor(self):
        pass

    def test_auto_fail(self):
        pass


if __name__ == '__main__':
    unittest.main()

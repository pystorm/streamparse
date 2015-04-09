from __future__ import absolute_import, print_function, unicode_literals

import itertools
import time
import unittest
try:
    from unittest import mock
    from unittest.mock import patch
except ImportError:
    import mock
    from mock import patch

from six.moves import range

from streamparse.storm import BatchingBolt, Bolt, Tuple


class BoltTests(unittest.TestCase):

    def setUp(self):
        self.bolt = Bolt()
        self.bolt.initialize({}, {})

    @patch.object(Bolt, 'send_message')
    def test_emit(self, send_message_mock):
        # A basic emit
        self.bolt.emit([1, 2, 3])
        send_message_mock.assert_called_with(
            {'command': 'emit', 'anchors': [], 'tuple': [1, 2, 3]}
        )

        # Emit with stream and anchors
        self.bolt.emit([1, 2, 3], stream='foo', anchors=[4, 5])
        send_message_mock.assert_called_with(
            {'command': 'emit',
             'stream': 'foo',
             'anchors': [4, 5],
             'tuple': [1, 2, 3]}
        )

        # Emit as a direct task
        self.bolt.emit([1, 2, 3], direct_task='other_bolt')
        send_message_mock.assert_called_with(
            {'command': 'emit',
             'anchors': [],
             'tuple': [1, 2, 3],
             'task': 'other_bolt'}
        )

    @patch.object(Bolt, 'send_message')
    def test_emit_many(self, send_message_mock):
        # emit_many will be tested once issue #44 is resolved
        # until then, it's a pain and not worth dealing with
        pass


    @patch.object(Bolt, 'send_message')
    def test_ack(self, send_message_mock):
        # ack an ID
        self.bolt.ack(42)
        send_message_mock.assert_called_with(
            {'command': 'ack', 'id': 42}
        )

        # ack a Tuple
        tup = Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        self.bolt.ack(tup)
        send_message_mock.assert_called_with(
            {'command': 'ack', 'id': 14}
        )

    @patch.object(Bolt, 'send_message')
    def test_fail(self, send_message_mock):
        # fail an ID
        self.bolt.fail(42)
        send_message_mock.assert_called_with(
            {'command': 'fail', 'id': 42}
        )

        # fail a Tuple
        tup = Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        self.bolt.ack(tup)
        send_message_mock.assert_called_with(
            {'command': 'ack', 'id': 14}
        )

    @patch.object(Bolt, 'process')
    @patch.object(Bolt, 'ack')
    @patch.object(Bolt, 'read_tuple')
    def test_run(self, read_tuple_mock, ack_mock, process_mock):
        tup = Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        read_tuple_mock.return_value = tup
        self.bolt._run()
        process_mock.assert_called_with(tup)
        self.assertListEqual(self.bolt._current_tups, [])

    @patch.object(Bolt, 'process')
    @patch.object(Bolt, 'ack')
    @patch.object(Bolt, 'read_tuple')
    def test_auto_ack(self, read_tuple_mock, ack_mock, process_mock):
        tup = Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        read_tuple_mock.return_value = tup

        # test auto-ack on (the default)
        self.bolt._run()
        ack_mock.assert_called_with(tup)
        ack_mock.reset_mock()

        # test auto-ack off
        self.bolt.auto_ack = False
        self.bolt._run()
        # Assert that this wasn't called, and print out what it was called with
        # otherwise.
        self.assertListEqual(ack_mock.call_args_list, [])

    @patch.object(Bolt, 'send_message')
    def test_auto_anchor(self, send_message_mock):
        tup = Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
        self.bolt._current_tups = [tup]

        # Test auto-anchor on (the default)
        self.bolt.emit([1, 2, 3])
        send_message_mock.assert_called_with(
            {'command': 'emit', 'anchors': [14], 'tuple': [1, 2, 3]}
        )

        # Test auto-anchor off
        self.bolt.auto_anchor = False
        self.bolt.emit([1, 2, 3])
        send_message_mock.assert_called_with(
            {'command': 'emit', 'anchors': [], 'tuple': [1, 2, 3]}
        )

        # Test overriding auto-anchor
        self.bolt.auto_anchor = True
        self.bolt.emit([1, 2, 3], anchors=[42])
        send_message_mock.assert_called_with(
            {'command': 'emit', 'anchors': [42], 'tuple': [1, 2, 3]}
        )

    @patch('sys.exit', new=lambda r: r)
    @patch.object(Bolt, 'read_handshake', new=lambda: (None, None))
    @patch.object(Bolt, 'raise_exception', new=lambda *a: None)
    @patch.object(Bolt, 'fail')
    @patch.object(Bolt, '_run')
    def test_auto_fail(self, _run_mock, fail_mock):
        tup = Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3])
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


@patch.object(Bolt, 'send_message', new=lambda *a: None)
@patch('streamparse.component.Component.send_message', new=lambda *a: None)
class BatchingBoltTests(unittest.TestCase):

    def setUp(self):
        # mock seconds between batches to speed the tests up
        self._orig_secs = BatchingBolt.secs_between_batches

        BatchingBolt.secs_between_batches = 0.05
        self.bolt = BatchingBolt()
        self.bolt.initialize({}, {})

        # Mock read_tuple and manually since it all needs to be mocked
        self.tups = [
            Tuple(14, 'some_spout', 'default', 'some_bolt', [1, 2, 3]),
            Tuple(15, 'some_spout', 'default', 'some_bolt', [4, 5, 6]),
            Tuple(16, 'some_spout', 'default', 'some_bolt', [7, 8, 9]),
        ]
        self._orig_read_tuple = self.bolt.read_tuple
        tups_cycle = itertools.cycle(self.tups)
        self.bolt.read_tuple = lambda: next(tups_cycle)

    def tearDown(self):
        # undo the mocking
        BatchingBolt.secs_between_batches = self._orig_secs
        self.bolt.read_tuple = self._orig_read_tuple

    @patch.object(BatchingBolt, 'process_batch')
    def test_batching(self, process_batch_mock):
        # Add a bunch of tuples
        for __ in range(3):
            self.bolt._run()

        # Wait a bit, and see if process_batch was called
        time.sleep(0.1)
        process_batch_mock.assert_called_with(None, self.tups[:3])

    @patch.object(BatchingBolt, 'process_batch')
    def test_group_key(self, process_batch_mock):
        # Change the group key to even/odd grouping
        self.bolt.group_key = lambda t: sum(t.values) % 2

        # Add a bunch of tuples
        for __ in range(3):
            self.bolt._run()

        # Wait a bit, and see if process_batch was called correctly
        time.sleep(0.1)
        process_batch_mock.assert_has_calls([
            mock.call(0, [self.tups[0], self.tups[2]]),
            mock.call(1, [self.tups[1]]),
        ], any_order=True)

    def _test_exception_handling(self):
        # TODO: Make this a real test (and remove leading underscore)
        # Make sure the exception gets from the worker thread to the main
        for i in range(1):
            self.bolt._run()
        self.assertRaises(NotImplementedError, lambda: time.sleep(0.1))

    @patch.object(BatchingBolt, 'ack')
    @patch.object(BatchingBolt, 'process_batch', new=lambda *args: None)
    def test_auto_ack(self, ack_mock):
        # Test auto-ack on (the default)
        for __ in range(3):
            self.bolt._run()
        time.sleep(0.1)
        ack_mock.assert_has_calls([
            mock.call(self.tups[0]),
            mock.call(self.tups[1]),
            mock.call(self.tups[2]),
        ], any_order=True)
        ack_mock.reset_mock()

        # Test auto-ack off
        self.bolt.auto_ack = False
        for __ in range(3):
            self.bolt._run()
        time.sleep(0.1)
        self.assertFalse(ack_mock.called)

    @patch.object(BatchingBolt, 'fail')
    @patch.object(BatchingBolt, 'process_batch', new=lambda *args: None)
    def test_auto_fail(self, fail_mock):
        # Test auto-fail on (the default)
        for __ in range(3):
            self.bolt._run()
        time.sleep(0.1)
        # All waiting tuples should have failed at this point
        fail_mock.assert_has_calls([
            mock.call(self.tups[0]),
            mock.call(self.tups[1]),
            mock.call(self.tups[2]),
        ], any_order=True)
        fail_mock.reset_mock()

        # Test auto-fail off
        self.bolt.auto_fail = False
        for __ in range(3):
            self.bolt._run()
        time.sleep(0.1)
        self.assertFalse(fail_mock.called)

    @patch.object(BatchingBolt, 'process_batch')
    @patch.object(BatchingBolt, 'fail')
    def test_auto_fail_partial(self, fail_mock, process_batch_mock):
        """Test processing failing when only some batches are done"""
        # NOTE: This test is currently broken because BatchingBolt is broken.
        #       If a batch fails, all subsequent batches need to fail too.
        #       Right now, only the current batch of tuples will be failed,
        #       leaving the rest to eventually time out. Not horrible, but
        #       definitely incorrect.
        # Change the group key just be the sum of values -- therefore 3 separate batches
        self.bolt.group_key = lambda t: sum(t.values)
        # Make sure we fail on the second batch
        work = {'status': True} # to avoid scoping problems
        def work_once(*args):
            if work['status']:
                work['status'] = False
            else:
                raise Exception('borkt')
        process_batch_mock.side_effect = work_once
        # Run the batches
        for __ in range(3):
            self.bolt._run()
        try:
            time.sleep(0.1)
        except Exception:
            pass
        # Only some tuples should have failed at this point. The key is that
        # all un-acked tuples should be failed, even for batches we haven't
        # started processing yet. Therefore
        self.assertEqual(fail_mock.call_count, 2)


if __name__ == '__main__':
    unittest.main()

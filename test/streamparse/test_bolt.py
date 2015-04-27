"""
Tests for Bolt and BatchingBolt classes
"""

from __future__ import absolute_import, print_function, unicode_literals

import itertools
import json
import logging
import time
import unittest
from io import BytesIO, StringIO

try:
    from unittest import mock
    from unittest.mock import patch
except ImportError:
    import mock
    from mock import patch

from six.moves import range

from streamparse.storm import BatchingBolt, Bolt, Component, Tuple


log = logging.getLogger(__name__)


class BoltTests(unittest.TestCase):

    def setUp(self):
        self.tup_dict = {'id': 14,
                         'comp': 'some_spout',
                         'stream': 'default',
                         'task': 'some_bolt',
                         'tuple': [1, 2, 3]}
        tup_json = "{}\nend\n".format(json.dumps(self.tup_dict))
        self.tup = Tuple(self.tup_dict['id'], self.tup_dict['comp'],
                         self.tup_dict['stream'], self.tup_dict['task'],
                         self.tup_dict['tuple'],)
        self.bolt = Bolt(input_stream=StringIO(tup_json),
                         output_stream=BytesIO())
        self.bolt.initialize({}, {})

    @patch.object(Bolt, 'send_message', autospec=True)
    def test_emit(self, send_message_mock):
        # A basic emit
        self.bolt.emit([1, 2, 3], need_task_ids=False)
        send_message_mock.assert_called_with(self.bolt, {'command': 'emit',
                                                         'anchors': [],
                                                         'tuple': [1, 2, 3],
                                                         'need_task_ids': False})

        # Emit with stream and anchors
        self.bolt.emit([1, 2, 3], stream='foo', anchors=[4, 5],
                       need_task_ids=False)
        send_message_mock.assert_called_with(self.bolt, {'command': 'emit',
                                                         'stream': 'foo',
                                                         'anchors': [4, 5],
                                                         'tuple': [1, 2, 3],
                                                         'need_task_ids': False})

        # Emit as a direct task
        self.bolt.emit([1, 2, 3], direct_task='other_bolt')
        send_message_mock.assert_called_with(self.bolt, {'command': 'emit',
                                                         'anchors': [],
                                                         'tuple': [1, 2, 3],
                                                         'task': 'other_bolt'})


    @patch.object(Bolt, 'send_message', autospec=True)
    def test_ack(self, send_message_mock):
        # ack an ID
        self.bolt.ack(42)
        send_message_mock.assert_called_with(self.bolt, {'command': 'ack',
                                                         'id': 42})

        # ack a Tuple
        self.bolt.ack(self.tup)
        send_message_mock.assert_called_with(self.bolt, {'command': 'ack',
                                                         'id': 14})

    @patch.object(Bolt, 'send_message', autospec=True)
    def test_fail(self, send_message_mock):
        # fail an ID
        self.bolt.fail(42)
        send_message_mock.assert_called_with(self.bolt, {'command': 'fail',
                                                         'id': 42})

        # fail a Tuple
        self.bolt.ack(self.tup)
        send_message_mock.assert_called_with(self.bolt, {'command': 'ack',
                                                         'id': 14})

    @patch.object(Bolt, 'process', autospec=True)
    @patch.object(Bolt, 'ack', autospec=True)
    def test_run(self, ack_mock, process_mock):
        self.bolt._run()
        process_mock.assert_called_with(self.bolt, self.tup)
        self.assertListEqual(self.bolt._current_tups, [])


    @patch.object(Bolt, 'process', autospec=True)
    @patch.object(Bolt, 'ack', autospec=True)
    def test_auto_ack_on(self, ack_mock, process_mock):
        # test auto-ack on (the default)
        self.bolt._run()
        ack_mock.assert_called_with(self.bolt, self.tup)

    @patch.object(Bolt, 'process', autospec=True)
    @patch.object(Bolt, 'ack', autospec=True)
    def test_auto_ack_off(self, ack_mock, process_mock):
        self.bolt.auto_ack = False
        self.bolt._run()
        # Assert that this wasn't called, and print out what it was called with
        # otherwise.
        self.assertListEqual(ack_mock.call_args_list, [])

    @patch.object(Bolt, 'send_message', autospec=True)
    def test_auto_anchor(self, send_message_mock):
        self.bolt._current_tups = [self.tup]
        # Test auto-anchor on (the default)
        self.bolt.emit([1, 2, 3], need_task_ids=False)
        send_message_mock.assert_called_with(self.bolt, {'command': 'emit',
                                                         'anchors': [14],
                                                         'tuple': [1, 2, 3],
                                                         'need_task_ids': False})

        # Test auto-anchor off
        self.bolt.auto_anchor = False
        self.bolt.emit([1, 2, 3], need_task_ids=False)
        send_message_mock.assert_called_with(self.bolt, {'command': 'emit',
                                                         'anchors': [],
                                                         'tuple': [1, 2, 3],
                                                         'need_task_ids': False})

        # Test overriding auto-anchor
        self.bolt.auto_anchor = True
        self.bolt.emit([1, 2, 3], anchors=[42], need_task_ids=False)
        send_message_mock.assert_called_with(self.bolt, {'command': 'emit',
                                                         'anchors': [42],
                                                         'tuple': [1, 2, 3],
                                                         'need_task_ids': False})

    @patch('sys.exit', new=lambda r: r)
    @patch.object(Bolt, 'read_handshake', new=lambda x: ({}, {}))
    @patch.object(Bolt, 'raise_exception', new=lambda *a: None)
    @patch.object(Bolt, 'fail', autospec=True)
    @patch.object(Bolt, '_run', autospec=True)
    def test_auto_fail_on(self, _run_mock, fail_mock):
        self.bolt._current_tups = [self.tup]
        # Make sure _run raises an exception
        def raiser(): # lambdas can't raise
            raise Exception('borkt')
        _run_mock.side_effect = raiser

        # test auto-fail on (the default)
        self.bolt.run()
        fail_mock.assert_called_with(self.bolt, self.tup)

    @patch('sys.exit', new=lambda r: r)
    @patch.object(Bolt, 'read_handshake', new=lambda x: ({}, {}))
    @patch.object(Bolt, 'raise_exception', new=lambda *a: None)
    @patch.object(Bolt, 'fail', autospec=True)
    @patch.object(Bolt, '_run', autospec=True)
    def test_auto_fail_off(self, _run_mock, fail_mock):
        self.bolt._current_tups = [self.tup]
        # Make sure _run raises an exception
        def raiser(): # lambdas can't raise
            raise Exception('borkt')
        _run_mock.side_effect = raiser

        # test auto-fail off
        self.bolt.auto_fail = False
        self.bolt.run()
        # Assert that this wasn't called, and print out what it was called with
        # otherwise.
        self.assertListEqual(fail_mock.call_args_list, [])

    @patch.object(Bolt, 'read_tuple', autospec=True)
    @patch.object(Bolt, 'send_message', autospec=True)
    def test_heartbeat_response(self, send_message_mock, read_tuple_mock):
        # Make sure we send sync for heartbeats
        read_tuple_mock.return_value = Tuple(id='foo', task=-1,
                                             stream='__heartbeat', values=[],
                                             component='__system')
        self.bolt._run()
        send_message_mock.assert_called_with(self.bolt, {'command': 'sync'})

    @patch.object(Bolt, 'read_tuple', autospec=True)
    @patch.object(Bolt, 'process_tick', autospec=True)
    def test_process_tick(self, process_tick_mock, read_tuple_mock):
        # Make sure we send sync for heartbeats
        read_tuple_mock.return_value = Tuple(id='foo', task=-1,
                                             component='__system',
                                             stream='__tick', values=[50])
        self.bolt._run()
        process_tick_mock.assert_called_with(self.bolt, 50)


class BatchingBoltTests(unittest.TestCase):

    def setUp(self):
        # mock seconds between batches to speed the tests up
        self._orig_secs = BatchingBolt.secs_between_batches

        BatchingBolt.secs_between_batches = 0.05

        self.tup_dicts = [{'id': 14,
                           'comp': 'some_spout',
                           'stream': 'default',
                           'task': 'some_bolt',
                           'tuple': [1, 2, 3]},
                          {'id': 15,
                           'comp': 'some_spout',
                           'stream': 'default',
                           'task': 'some_bolt',
                           'tuple': [4, 5, 6]},
                          {'id': 16,
                           'comp': 'some_spout',
                           'stream': 'default',
                           'task': 'some_bolt',
                           'tuple': [7, 8, 9]}]
        tups_json = '\nend\n'.join([json.dumps(tup_dict) for tup_dict in
                                    self.tup_dicts] + [''])
        self.tups = [Tuple(tup_dict['id'], tup_dict['comp'], tup_dict['stream'],
                           tup_dict['task'], tup_dict['tuple']) for tup_dict in
                     self.tup_dicts]
        self.bolt = BatchingBolt(input_stream=StringIO(tups_json),
                                 output_stream=BytesIO())
        self.bolt.initialize({}, {})

    def tearDown(self):
        # undo the mocking
        BatchingBolt.secs_between_batches = self._orig_secs

    @patch.object(BatchingBolt, 'process_batch', autospec=True)
    def test_batching(self, process_batch_mock):
        # Add a bunch of tuples
        for __ in range(3):
            self.bolt._run()

        # Wait a bit, and see if process_batch was called
        time.sleep(0.5)
        process_batch_mock.assert_called_with(self.bolt, None, self.tups[:3])

    @patch.object(BatchingBolt, 'process_batch', autospec=True)
    def test_group_key(self, process_batch_mock):
        # Change the group key to even/odd grouping
        self.bolt.group_key = lambda t: sum(t.values) % 2

        # Add a bunch of tuples
        for __ in range(3):
            self.bolt._run()

        # Wait a bit, and see if process_batch was called correctly
        time.sleep(0.5)
        process_batch_mock.assert_has_calls([mock.call(self.bolt, 0,
                                                       [self.tups[0],
                                                        self.tups[2]]),
                                             mock.call(self.bolt, 1,
                                                       [self.tups[1]])],
                                            any_order=True)

    def test_exception_handling(self):
        # Make sure the exception gets from the worker thread to the main
        with self.assertRaises(NotImplementedError):
            self.bolt._run()
            time.sleep(0.5)

    @patch.object(BatchingBolt, 'ack', autospec=True)
    @patch.object(BatchingBolt, 'process_batch', new=lambda *args: None)
    def test_auto_ack_on(self, ack_mock):
        # Test auto-ack on (the default)
        for __ in range(3):
            self.bolt._run()
        time.sleep(0.5)
        ack_mock.assert_has_calls([mock.call(self.bolt, self.tups[0]),
                                   mock.call(self.bolt, self.tups[1]),
                                   mock.call(self.bolt, self.tups[2])],
                                  any_order=True)

    @patch.object(BatchingBolt, 'ack', autospec=True)
    @patch.object(BatchingBolt, 'process_batch', new=lambda *args: None)
    def test_auto_ack_off(self, ack_mock):
        # Test auto-ack off
        self.bolt.auto_ack = False
        for __ in range(3):
            self.bolt._run()
        time.sleep(0.5)
        # Assert that this wasn't called, and print out what it was called with
        # otherwise.
        self.assertListEqual(ack_mock.call_args_list, [])


    @patch.object(BatchingBolt, '_handle_worker_exception', autospec=True)
    @patch.object(BatchingBolt, 'fail', autospec=True)
    def test_auto_fail_on(self, fail_mock, worker_exception_mock):
        # Need to re-register signal handler with mocked version, because
        # mock gets created after handler was originally registered.
        self.setUp()
        # Test auto-fail on (the default)
        for __ in range(3):
            self.bolt._run()
        time.sleep(0.5)

        # All waiting tuples should have failed at this point
        fail_mock.assert_has_calls([mock.call(self.bolt, self.tups[0]),
                                    mock.call(self.bolt, self.tups[1]),
                                    mock.call(self.bolt, self.tups[2])],
                                   any_order=True)
        self.assertEqual(worker_exception_mock.call_count, 1)

    @patch.object(BatchingBolt, '_handle_worker_exception', autospec=True)
    @patch.object(BatchingBolt, 'fail', autospec=True)
    def test_auto_fail_off(self, fail_mock, worker_exception_mock):
        # Need to re-register signal handler with mocked version, because
        # mock gets created after handler was originally registered.
        self.setUp()
        self.bolt.auto_fail = False
        for __ in range(3):
            self.bolt._run()
        time.sleep(0.5)
        # Assert that this wasn't called, and print out what it was called with
        # otherwise.
        self.assertListEqual(fail_mock.call_args_list, [])
        self.assertEqual(worker_exception_mock.call_count, 1)

    @patch.object(BatchingBolt, '_handle_worker_exception', autospec=True)
    @patch.object(BatchingBolt, 'process_batch', autospec=True)
    @patch.object(BatchingBolt, 'fail', autospec=True)
    def test_auto_fail_partial(self, fail_mock, process_batch_mock,
                               worker_exception_mock):
        # Need to re-register signal handler with mocked version, because
        # mock gets created after handler was originally registered.
        self.setUp()
        # Change the group key just be the sum of values, which makes 3 separate
        # batches
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
        time.sleep(0.5)
        # Only some tuples should have failed at this point. The key is that
        # all un-acked tuples should be failed, even for batches we haven't
        # started processing yet.
        self.assertEqual(fail_mock.call_count, 2)
        self.assertEqual(worker_exception_mock.call_count, 1)

    @patch.object(BatchingBolt, 'read_tuple', autospec=True)
    @patch.object(BatchingBolt, 'send_message', autospec=True)
    def test_heartbeat_response(self, send_message_mock, read_tuple_mock):
        # Make sure we send sync for heartbeats
        read_tuple_mock.return_value = Tuple(id='foo', task=-1,
                                             stream='__heartbeat', values=[],
                                             component='__system')
        self.bolt._run()
        send_message_mock.assert_called_with(self.bolt, {'command': 'sync'})

    @patch.object(BatchingBolt, 'read_tuple', autospec=True)
    @patch.object(BatchingBolt, 'process_tick', autospec=True)
    def test_process_tick(self, process_tick_mock, read_tuple_mock):
        # Make sure we send sync for heartbeats
        read_tuple_mock.return_value = Tuple(id='foo', task=-1,
                                             component='__system',
                                             stream='__tick', values=[50])
        self.bolt._run()
        process_tick_mock.assert_called_with(self.bolt, 50)



if __name__ == '__main__':
    unittest.main()

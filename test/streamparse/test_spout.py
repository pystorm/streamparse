"""
Tests for Spout class
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
import unittest
from io import BytesIO

try:
    from unittest import mock
    from unittest.mock import patch
except ImportError:
    import mock
    from mock import patch

from streamparse.storm import Spout, Tuple


log = logging.getLogger(__name__)


class SpoutTests(unittest.TestCase):

    def setUp(self):
        self.tup_dict = {'id': 14,
                         'comp': 'some_spout',
                         'stream': 'default',
                         'task': 'some_spout',
                         'tuple': [1, 2, 3]}
        self.tup = Tuple(self.tup_dict['id'], self.tup_dict['comp'],
                         self.tup_dict['stream'], self.tup_dict['task'],
                         self.tup_dict['tuple'],)
        self.spout = Spout(input_stream=BytesIO(),
                           output_stream=BytesIO())
        self.spout.initialize({}, {})
        self.spout.logger = log

    @patch.object(Spout, 'send_message', autospec=True)
    def test_emit(self, send_message_mock):
        # A basic emit
        self.spout.emit([1, 2, 3], need_task_ids=False)
        send_message_mock.assert_called_with(self.spout, {'command': 'emit',
                                                          'tuple': [1, 2, 3],
                                                          'need_task_ids': False})

        # Emit as a direct task
        self.spout.emit([1, 2, 3], direct_task='other_spout')
        send_message_mock.assert_called_with(self.spout, {'command': 'emit',
                                                          'tuple': [1, 2, 3],
                                                          'task': 'other_spout'})
        # Reliable emit
        self.spout.emit([1, 2, 3], tup_id='foo', need_task_ids=False)
        send_message_mock.assert_called_with(self.spout, {'command': 'emit',
                                                          'tuple': [1, 2, 3],
                                                          'need_task_ids': False,
                                                          'id': 'foo'})

        # Reliable emit as direct task
        self.spout.emit([1, 2, 3], tup_id='foo', direct_task='other_spout')
        send_message_mock.assert_called_with(self.spout, {'command': 'emit',
                                                          'tuple': [1, 2, 3],
                                                          'task': 'other_spout',
                                                          'id': 'foo'})


    @patch.object(Spout, 'send_message', autospec=True)
    def test_emit_many(self, send_message_mock):
        # A basic emit
        self.spout.emit_many([[1, 2, 3], [4, 5, 6]], need_task_ids=False)
        send_message_mock.assert_has_calls([mock.call(self.spout,
                                                      {'command': 'emit',
                                                       'tuple': [1, 2, 3],
                                                       'need_task_ids': False}),
                                            mock.call(self.spout,
                                                      {'command': 'emit',
                                                       'tuple': [4, 5, 6],
                                                       'need_task_ids': False})])

        # Reliable emit
        send_message_mock.reset_mock()
        self.spout.emit_many([[1, 2, 3], [4, 5, 6]], tup_ids=['foo', 'bar'],
                             need_task_ids=False)
        send_message_mock.assert_has_calls([mock.call(self.spout,
                                                      {'command': 'emit',
                                                       'tuple': [1, 2, 3],
                                                       'need_task_ids': False,
                                                       'id': 'foo'}),
                                            mock.call(self.spout,
                                                      {'command': 'emit',
                                                       'tuple': [4, 5, 6],
                                                       'need_task_ids': False,
                                                       'id': 'bar'})])

        # Emit as a direct task
        send_message_mock.reset_mock()
        self.spout.emit_many([[1, 2, 3], [4, 5, 6]], direct_task='other_spout')
        send_message_mock.assert_has_calls([mock.call(self.spout,
                                                      {'command': 'emit',
                                                       'tuple': [1, 2, 3],
                                                       'task': 'other_spout'}),
                                            mock.call(self.spout,
                                                      {'command': 'emit',
                                                       'tuple': [4, 5, 6],
                                                       'task': 'other_spout'})])

    @patch.object(Spout, 'read_command', autospec=True,
                  return_value={'command': 'ack', 'id': 1234})
    @patch.object(Spout, 'ack', autospec=True)
    def test_ack(self, ack_mock, read_command_mock):
        # Make sure ack gets called
        self.spout._run()
        read_command_mock.assert_called_with(self.spout)
        ack_mock.assert_called_with(self.spout, 1234)

    @patch.object(Spout, 'read_command', autospec=True,
                  return_value={'command': 'fail', 'id': 1234})
    @patch.object(Spout, 'fail', autospec=True)
    def test_fail(self, fail_mock, read_command_mock):
        # Make sure fail gets called
        self.spout._run()
        read_command_mock.assert_called_with(self.spout)
        fail_mock.assert_called_with(self.spout, 1234)

    @patch.object(Spout, 'read_command', autospec=True,
                  return_value={'command': 'next', 'id': 1234})
    @patch.object(Spout, 'next_tuple', autospec=True)
    def test_next_tuple(self, next_tuple_mock, read_command_mock):
        self.spout._run()
        read_command_mock.assert_called_with(self.spout)
        self.assertEqual(next_tuple_mock.call_count, 1)


if __name__ == '__main__':
    unittest.main()

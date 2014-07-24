from __future__ import absolute_import, print_function, unicode_literals

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

    def test_emit_many(self):
        pass

    @patch('streamparse.bolt.send_message')
    def test_ack(self, send_message_mock):
        # ack an ID
        self.bolt.ack(14)
        send_message_mock.assert_called_with(
            {'command': 'ack', 'id': 14}
        )
        # TODO: Ack a Tuple

    @patch('streamparse.bolt.send_message')
    def test_fail(self, send_message_mock):
        # fail an ID
        self.bolt.fail(14)
        send_message_mock.assert_called_with(
            {'command': 'fail', 'id': 14}
        )
        # TODO: Ack a Tuple

    def test_run(self):
        pass # TODO: That infinite loop is going to make this one tricky


if __name__ == '__main__':
    unittest.main()

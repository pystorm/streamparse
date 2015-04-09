from __future__ import absolute_import, print_function, unicode_literals

import itertools
import json
import unittest
try:
    from unittest import mock
    from unittest.mock import patch
except ImportError:
    import mock
    from mock import patch

from six import PY3

from streamparse import ipc

class IPCTests(unittest.TestCase):

    def setup_readlines(self, stdin_mock, lines):
        """mocking readline isn't simple because it's called multiple times"""
        lines = itertools.cycle(lines)
        stdin_mock.readline.side_effect = lambda: lines.next()

    @patch('streamparse.ipc._stdin')
    def test_read_message_lines(self, stdin_mock):
        lines = [
            'test input not json formatted\n',
            'another line of input\n',
            'end\n',
        ]
        self.setup_readlines(stdin_mock, lines)
        linereader = ipc.read_message_lines()
        self.assertListEqual(
            list(linereader),
            [l[:-1] for l in lines[:-1]] # no 'end' and trims newlines
        )

    @patch('streamparse.ipc._stdin')
    def test_read_message_lines_toolong(self, stdin_mock):
        lines = [
            'test input not json formatted\n',
            'uh oh {}'.format('*' * ipc._MAX_MESSAGE_SIZE),
            'end\n',
        ]
        self.setup_readlines(stdin_mock, lines)
        linereader = ipc.read_message_lines()
        self.assertRaises(
            ipc.StormIPCException,
            lambda: list(linereader)
        )

    @patch('streamparse.ipc._stdout')
    def test_send_message(self, stdout_mock):
        msg = {'command': 'testing', 'id': '42'}
        ipc.send_message(msg)

        wrapped = "{}\nend\n".format(json.dumps(msg)).encode('utf-8')
        if PY3:
            stdout_mock.buffer.write.assert_called_with(wrapped)
            stdout_mock.buffer.flush.assert_called_with()
        else:
            stdout_mock.write.assert_called_with(wrapped)
        stdout_mock.flush.assert_called_with()


if __name__ == '__main__':
    unittest.main()

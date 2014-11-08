from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess
import time
import unittest

from .util import ShellProcess, ShellComponentTestCaseMixin


_multiprocess_can_split_ = True

class ShellSpoutTester(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_spout.py"

    def test_next_tuple(self):
        msg = {"command": "next"}

        res = self.shell_proc.query_subprocess(msg)
        self.assertEqual(len(res), 2)
        cmd = res[0]
        self.assertDictEqual({"command": "emit", "tuple": ["test"]}, cmd)
        cmd = res[1]
        self.assertDictEqual({"command": "sync"}, cmd)

    def test_ack(self):
        msg = {"command": "ack", "id": "123456"}
        res = self.shell_proc.query_subprocess(msg)

        self.assertEqual(len(res), 1)

        cmd = res[0]
        self.assertDictEqual({"command": "sync"}, cmd)

    def test_fail(self):
        msg = {"command": "fail", "id": "123456"}
        res = self.shell_proc.query_subprocess(msg)

        self.assertEqual(len(res), 1)

        cmd = res[0]
        self.assertDictEqual({"command": "sync"}, cmd)


if __name__ == '__main__':
    unittest.main()

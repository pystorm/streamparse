from __future__ import print_function, absolute_import
import subprocess
import unittest
import os
import sys
import time

from .util import ShellProcess


_ROOT = os.path.dirname(os.path.realpath(__file__))
def here(*x):
    return os.path.join(_ROOT, *x)


class ShellSpoutTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        args = ["python", here("dummy_spout.py")]
        cls.proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        print("Waiting for subprocess to start...")
        time.sleep(1)  # time for the subprocess to start
        if cls.proc.poll() is not None:
            raise Exception("Could not create subprocess.\n{}"
                            .format("".join(cls.proc.stderr.readlines())))
        cls.shell_proc = ShellProcess(cls.proc.stdout, cls.proc.stdin)

    def test_1_initial_handshake(self):
        msg = {
            "conf": {},
            "context": {},
            "pidDir": here()
        }
        ShellSpoutTester.shell_proc.write_message(msg)
        res = ShellSpoutTester.shell_proc.read_message()

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("pid"), ShellSpoutTester.proc.pid)
        pid = str(res["pid"])
        self.assertTrue(os.path.exists(here(pid)))
        self.assertTrue(os.path.isfile(here(pid)))

    def test_2_next_tuple(self):
        msg = {"command": "next"}
        res = ShellSpoutTester.shell_proc.query_subprocess(msg)

        self.assertEqual(len(res), 2)

        cmd = res[0]
        self.assertDictEqual({"command": "emit", "tuple": ["test"]}, cmd)

        cmd = res[1]
        self.assertDictEqual({"command": "sync"}, cmd)

    def test_3_ack(self):
        msg = {"command": "ack", "id": "123456"}
        res = ShellSpoutTester.shell_proc.query_subprocess(msg)

        self.assertEqual(len(res), 1)

        cmd = res[0]
        self.assertDictEqual({"command": "sync"}, cmd)

    def test_4_fail(self):
        msg = {"command": "fail", "id": "123456"}
        res = ShellSpoutTester.shell_proc.query_subprocess(msg)

        self.assertEqual(len(res), 1)

        cmd = res[0]
        self.assertDictEqual({"command": "sync"}, cmd)

    @classmethod
    def tearDownClass(cls):
        os.remove(here(str(cls.proc.pid)))
        cls.proc.kill()

if __name__ == '__main__':
    unittest.main()

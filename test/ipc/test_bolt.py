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


class ShellBoltTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        args = ["python", here("dummy_bolt.py")]
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
        ShellBoltTester.shell_proc.write_message(msg)
        res = ShellBoltTester.shell_proc.read_message()

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("pid"), ShellBoltTester.proc.pid)
        pid = str(res["pid"])
        self.assertTrue(os.path.exists(here(pid)))
        self.assertTrue(os.path.isfile(here(pid)))

    def test_2_echo_tuple(self):
        msg = {
            "id": "2285924946354050200",
            "comp": "word-spout",
            "stream": "default",
            "task": 0,
            "tuple": ["snow white and the seven dwarfs", "field2", 3, 4.252]
        }
        ShellBoltTester.shell_proc.write_message(msg)
        res = ShellBoltTester.shell_proc.read_message()

        # DummyBolt should simply echo any tuple sent in to it
        self.assertEqual(res.get("command"), "emit")
        self.assertEqual(msg["tuple"], res.get("tuple"))

    def test_3_ack_tuple(self):
        msg = {
            "id": "ack_me",
            "comp": "word-spout",
            "stream": "default",
            "task": 0,
            "tuple": ["snow white and the seven dwarfs", "field2", 3, 4.252]
        }
        ShellBoltTester.shell_proc.write_message(msg)
        res = ShellBoltTester.shell_proc.read_message()
        self.assertEqual(res.get("command"), "emit")
        self.assertEqual(msg["tuple"], res.get("tuple"))

        res = ShellBoltTester.shell_proc.read_message()
        self.assertEqual(res, {"command": "ack", "id": msg["id"]})

    def test_4_fail_tuple(self):
        msg = {
            "id": "fail_me",
            "comp": "word-spout",
            "stream": "default",
            "task": 0,
            "tuple": ["snow white and the seven dwarfs", "field2", 3, 4.252]
        }

        ShellBoltTester.shell_proc.write_message(msg)
        res = ShellBoltTester.shell_proc.read_message()
        self.assertEqual(res.get("command"), "emit")
        self.assertEqual(msg["tuple"], res.get("tuple"))

        res = ShellBoltTester.shell_proc.read_message()
        self.assertEqual(res, {"command": "fail", "id": msg["id"]})

    def test_5_emit_many(self):
        msg = {
            "id": "emit_many",
            "comp": "word-spout",
            "stream": "default",
            "task": 0,
            "tuple": ["snow white and the seven dwarfs", "field2", 3, 4.252]
        }
        ShellBoltTester.shell_proc.write_message(msg)
        for i in xrange(5):
            res = ShellBoltTester.shell_proc.read_message()
            self.assertEqual(res.get("tuple"), msg["tuple"])


    @classmethod
    def tearDownClass(cls):
        os.remove(here(str(cls.proc.pid)))
        cls.proc.kill()

if __name__ == '__main__':
    unittest.main()

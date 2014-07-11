from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess
import time
import unittest

from test.ipc.util import ShellProcess


_ROOT = os.path.dirname(os.path.realpath(__file__))
def here(*x):
    return os.path.join(_ROOT, *x)


class BasicBoltTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        args = ["python", here("dummy_basic_bolt.py")]
        cls.proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        print("Waiting for subprocess to start...")
        time.sleep(1)  # time for the subprocess to start
        if cls.proc.poll() is not None:
            raise Exception("Could not create subprocess.\n{}"
                            .format(cls.proc.stderr.read().decode('utf-8')))
        cls.shell_proc = ShellProcess(cls.proc.stdout, cls.proc.stdin)

    def test_1_initial_handshake(self):
        msg = {
            "conf": {},
            "context": {},
            "pidDir": here()
        }
        BasicBoltTester.shell_proc.write_message(msg)
        res = BasicBoltTester.shell_proc.read_message()

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("pid"), BasicBoltTester.proc.pid)
        pid = str(res["pid"])
        self.assertTrue(os.path.exists(here(pid)))
        self.assertTrue(os.path.isfile(here(pid)))

    def test_2_auto_ack(self):
        msg = {
            "id": "noop",
            "comp": "word-spout",
            "stream": "default",
            "task": 0,
            "tuple": ["snow white and the seven dwarfs", "field2", 3, 4.252]
        }
        BasicBoltTester.shell_proc.write_message(msg)
        res = BasicBoltTester.shell_proc.read_message()
        self.assertEqual(res, {"command": "ack", "id": msg["id"]})

    def test_3_auto_anchor(self):
        msg = {
            "id": "emit",
            "comp": "word-spout",
            "stream": "default",
            "task": 0,
            "tuple": ["snow white and the seven dwarfs", "field2", 3, 4.252]
        }

        BasicBoltTester.shell_proc.write_message(msg)
        res = BasicBoltTester.shell_proc.read_message()
        self.assertEqual(res.get("command"), "emit")
        self.assertEqual(msg["tuple"], res.get("tuple"))
        self.assertEqual([msg["id"],], res.get("anchors"))


    @classmethod
    def tearDownClass(cls):
        os.remove(here(str(cls.proc.pid)))
        cls.proc.kill()

if __name__ == '__main__':
    unittest.main()

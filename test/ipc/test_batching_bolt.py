from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess
import time
import unittest

from six.moves import range

from .util import ShellProcess

_ROOT = os.path.dirname(os.path.realpath(__file__))
def here(*x):
    return os.path.join(_ROOT, *x)


class ShellBatchingBoltTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        args = ["python", here("dummy_batching_bolt.py")]
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
        ShellBatchingBoltTester.shell_proc.write_message(msg)
        res = ShellBatchingBoltTester.shell_proc.read_message()

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("pid"), ShellBatchingBoltTester.proc.pid)
        pid = str(res["pid"])
        self.assertTrue(os.path.exists(here(pid)))
        self.assertTrue(os.path.isfile(here(pid)))

    def test_2_ack_tuple(self):
        msg = {
            "id": "2285924946354050200",
            "comp": "word-spout",
            "stream": "default",
            "task": 0,
            "tuple": ["snow white and the seven dwarfs", "field2", 3, 4.252],
        }
        ShellBatchingBoltTester.shell_proc.write_message(msg)

        res = ShellBatchingBoltTester.shell_proc.read_message()
        self.assertEqual(res.get("command"), "emit")
        self.assertEqual(res.get("tuple"),
                         ["snow white and the seven dwarfs", msg["id"]])

        res = ShellBatchingBoltTester.shell_proc.read_message()
        self.assertEqual(res.get("command"), "ack")
        self.assertEqual(res.get("id"), msg["id"])

    def test_3_multi_ack(self):
        msg = {
            "id": None,
            "comp": "word-spout",
            "stream": "default",
            "task": 0,
            "tuple": ["snow white and the seven dwarfs", "field2", 3, 4.252],
        }
        for i in range(5):
            msg["id"] = str(i)
            ShellBatchingBoltTester.shell_proc.write_message(msg)
        time.sleep(2.5)
        # Ensure that we have a series of emits followed by a series of acks
        for i in range(5):
            res = ShellBatchingBoltTester.shell_proc.read_message()
            self.assertEqual(res.get("command"), "emit")
            self.assertEqual(res.get("tuple"),
                             ["snow white and the seven dwarfs", str(i)])
        for i in range(5):
            res = ShellBatchingBoltTester.shell_proc.read_message()
            self.assertEqual(res.get("command"), "ack")
            self.assertEqual(res.get("id"), str(i))

    def test_4_batches(self):
        # Create two batches the "mike" batch and the "lida" batch
        messages = (
            {
                "id": "0",
                "comp": "word-spout",
                "stream": "default",
                "task": 0,
                "tuple": ["mike", "smith"],
            },
            {
                "id": "1",
                "comp": "word-spout",
                "stream": "default",
                "task": 0,
                "tuple": ["mike", "sukmanowsky"],
            },
            {
                "id": "3",
                "comp": "word-spout",
                "stream": "default",
                "task": 0,
                "tuple": ["lida", "elias"],
            },
            {
                "id": "4",
                "comp": "word-spout",
                "stream": "default",
                "task": 0,
                "tuple": ["lida", "smith"],
            },
        )
        for message in messages:
            ShellBatchingBoltTester.shell_proc.write_message(message)

        time.sleep(2.5)

        results = []
        # should have series of emits, then series of acks repeated twice
        for i in range(2*2*2):
            results.append(ShellBatchingBoltTester.shell_proc.read_message())

        expected_commands = ["emit"] * 2
        expected_commands += ["ack"] * 2
        expected_commands += ["emit"] * 2
        expected_commands += ["ack"] * 2
        for i, command in enumerate(expected_commands):
            res = results[i]
            self.assertEqual(res.get("command"), command)

    def test_5_worker_exception(self):
        msg = {
            "id": "0",
            "comp": "word-spout",
            "stream": "default",
            "task": 0,
            "tuple": ["fail"],
        }
        ShellBatchingBoltTester.shell_proc.write_message(msg)
        res = ShellBatchingBoltTester.shell_proc.read_message()
        self.assertEqual(res.get("command"), "log")
        self.assertIn("Exception", res.get("msg"))

        res = ShellBatchingBoltTester.shell_proc.read_message()
        self.assertEqual(res.get("command"), "sync")

        self.assertRaises(Exception,
                          ShellBatchingBoltTester.shell_proc.read_message)

    @classmethod
    def tearDownClass(cls):
        os.remove(here(str(cls.proc.pid)))
        cls.proc.kill()


if __name__ == '__main__':
    unittest.main()

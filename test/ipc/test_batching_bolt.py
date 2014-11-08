from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess
import time
import unittest

from six.moves import range, zip

from .util import ShellProcess, ShellComponentTestCaseMixin, get_message


_multiprocess_can_split_ = True

BATCH = (
    get_message(id="0", tuple=["mike"]),
    get_message(id="1", tuple=["mike"]),
    get_message(id="2", tuple=["lida"]),
    get_message(id="3", tuple=["lida"]),
)

class BatchingBoltTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_batching_bolt.py"

    def test_single_tuple(self):
        msg = get_message()

        self.shell_proc.write_message(msg)
        res = self.shell_proc.read_message()

        self.assertEqual(res["command"], "emit")
        self.assertEqual(res["tuple"],
                         ["snow white and the seven dwarfs", msg["id"]])

    def test_multi_tuple(self):
        msg = get_message()
        for i in range(5):
            msg["id"] = str(i)
            self.shell_proc.write_message(msg)

        time.sleep(1.5)  # Wait for batch to complete
        # Ensure that we have a series of emits
        for i in range(5):
            res = self.shell_proc.read_message()
            self.assertEqual(res.get("command"), "emit")
            self.assertEqual(res.get("tuple"),
                             ["snow white and the seven dwarfs", str(i)])

    def test_batches(self):
        for message in BATCH:
            self.shell_proc.write_message(message)

        time.sleep(1.5)  # wait for batch to complete

        expected_commands = ["emit"] * 4

        results = []
        for i in range(len(expected_commands)):
            results.append(self.shell_proc.read_message())

        for actual, expected in zip(results, expected_commands):
            self.assertEqual(actual["command"], expected)

    # TODO: Test emit_many


class BatchingBoltExceptionTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_batching_bolt.py"

    def test_worker_exception(self):
        msg = get_message(tuple=["fail"])

        self.shell_proc.write_message(msg)
        time.sleep(1.5)  # wait for batch to complete

        for i in range(2):
            # we'll get an error message from the _batcher thread and then
            # the main thread
            res = self.shell_proc.read_message()
            self.assertEqual(res["command"], "log")
            self.assertIn("Exception", res["msg"])

            res = self.shell_proc.read_message()
            self.assertEqual(res["command"], "sync")

        # Ensure bolt exited
        self.assertRaises(Exception, self.shell_proc.read_message)


class BatchingBoltAutoAckTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_batching_bolt_auto_ack.py"

    def test_auto_ack(self):
        for message in BATCH:
            self.shell_proc.write_message(message)

        time.sleep(1.5)  # wait for batch to complete

        expected_commands = ["emit", "ack", "ack", "emit", "ack", "ack"]
        for cmd in expected_commands:
            msg = self.shell_proc.read_message()
            self.assertEqual(msg["command"], cmd)


class BatchingBoltAutoAnchorTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_batching_bolt_auto_anchor.py"

    def test_auto_anchor(self):
        for message in BATCH:
            self.shell_proc.write_message(message)

        time.sleep(1.5)  # wait for batch to complete

        expected_commands = ["emit", "emit"]

        results = []
        for i in range(len(expected_commands)):
            results.append(self.shell_proc.read_message())

        for actual, expected in zip(results, expected_commands):
            self.assertEqual(actual["command"], expected)
            self.assertEqual(len(actual["anchors"]), 2)


class BatchingBoltAutoFailTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_batching_bolt_auto_fail.py"

    def test_auto_fail(self):
        for message in BATCH:
            self.shell_proc.write_message(message)

        time.sleep(1.5)  # wait for batch to complete

        # log the exception and sync up, then fail all tuples in the current
        # batch
        expected_commands = ["log", "sync", "fail", "fail"]
        for i in range(len(expected_commands)):
            res = self.shell_proc.read_message()
            self.assertEqual(res["command"], expected_commands[i])


if __name__ == '__main__':
    unittest.main()

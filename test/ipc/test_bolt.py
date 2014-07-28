from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess
import time
import unittest

from .util import ShellProcess, ShellComponentTestCaseMixin, get_message


_multiprocess_can_split_ = True

class BoltTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_bolt.py"

    def test_echo_tuple(self):
        msg = get_message()
        self.shell_proc.write_message(msg)

        res = self.shell_proc.read_message()
        # DummyBolt should simply echo any tuple sent in to it
        self.assertEqual(res["command"], "emit")
        self.assertEqual(msg["tuple"], res["tuple"])
        self.shell_proc.write_message([1])  # send fake task id

    def test_ack_tuple(self):
        msg = get_message(id="ack_me")
        self.shell_proc.write_message(msg)

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "emit")
        self.assertEqual(msg["tuple"], res["tuple"])
        self.shell_proc.write_message([1])  # send fake task id

        res = self.shell_proc.read_message()
        self.assertEqual(res, {"command": "ack", "id": msg["id"]})

    def test_fail_tuple(self):
        msg = get_message(id="fail_me")
        self.shell_proc.write_message(msg)

        res = self.shell_proc.read_message()
        self.assertEqual(res, {"command": "fail", "id": msg["id"]})

    def test_emit_stream(self):
        msg = get_message(id="stream-words")
        self.shell_proc.write_message(msg)

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "emit")
        self.assertEqual(res["stream"], "words")
        self.assertEqual(res["tuple"], msg["tuple"])
        self.shell_proc.write_message([1])  # send fake task id

    def test_emit_anchoring(self):
        msg = get_message(id="anchor|1,2,3")
        self.shell_proc.write_message(msg)

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "emit")
        self.assertEqual(res["anchors"], ["1", "2", "3"])
        self.assertEqual(res["tuple"], msg["tuple"])
        self.shell_proc.write_message([1])  # send fake task id

    def test_emit_direct_task(self):
        msg = get_message(id="direct_task|12")
        self.shell_proc.write_message(msg)

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "emit")
        self.assertEqual(res["task"], 12)
        self.assertEqual(res["tuple"], msg["tuple"])

    def test_emit_many(self):
        msg = get_message(id="emit_many")
        self.shell_proc.write_message(msg)

        for i in range(5):
            res = self.shell_proc.read_message()
            self.assertEqual(res["tuple"], msg["tuple"])
            self.shell_proc.write_message([1])  # send fake task id

    # TODO: test emit_many for stream, anchoring, direct_task


class BoltExceptionTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_bolt.py"

    def test_exception(self):
        """Ensure that exceptions raised in the bolt send proper log messages
        before exiting. In a separate test case as the process immediately
        exits after an exception is raised.
        """
        msg = get_message(id="exception")

        self.shell_proc.write_message(msg)
        res = self.shell_proc.read_message()

        self.assertEqual(res["command"], "log")
        self.assertIn("Exception: ", res["msg"])

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "sync")

        # Ensure exit code of 1 from bolt
        time.sleep(0.5)
        self.assertEqual(self.proc.poll(), 1)


class BoltAutoAckTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_bolt_auto_ack.py"

    def test_emit_auto_ack(self):
        msg = get_message()

        self.shell_proc.write_message(msg)
        res = self.shell_proc.read_message()

        self.assertEqual(res["command"], "emit")
        self.assertEqual(msg["tuple"], res["tuple"])
        self.shell_proc.write_message([1]) # send fake task id

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "ack")
        self.assertEqual(res["id"], msg["id"])

    def test_emit_many_auto_ack(self):
        msg = get_message(id="emit_many")

        self.shell_proc.write_message(msg)
        for i in range(5):
            res = self.shell_proc.read_message()
            self.assertEqual(res["command"], "emit")
            self.assertEqual(res["tuple"], msg["tuple"])
            self.shell_proc.write_message([1])  # send fake task id

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "ack")
        self.assertEqual(res["id"], msg["id"])


class BoltAutoAnchorTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_bolt_auto_anchor.py"

    def test_emit_auto_anchor(self):
        msg = get_message()

        self.shell_proc.write_message(msg)
        res = self.shell_proc.read_message()

        # DummyBolt should simply echo any tuple sent in to it
        self.assertEqual(res["command"], "emit")
        self.assertEqual(msg["tuple"], res["tuple"])
        self.assertEqual(res["anchors"], [msg["id"]])
        self.shell_proc.write_message([1])  # send fake task id

    def test_emit_many_auto_anchor(self):
        msg = get_message(id="emit_many")

        self.shell_proc.write_message(msg)

        for i in range(5):
            res = self.shell_proc.read_message()
            self.assertEqual(res["command"], "emit")
            self.assertEqual(msg["tuple"], res["tuple"])
            self.assertEqual(res["anchors"], [msg["id"]])
            self.shell_proc.write_message([1])  # send fake task id


class BoltAutoFailTest(ShellComponentTestCaseMixin, unittest.TestCase):

    component = "dummy_bolt_auto_fail.py"

    def test_auto_fail(self):
        msg = get_message()

        self.shell_proc.write_message(msg)

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "log")
        self.assertIn("Exception: ", res["msg"])

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "sync")

        res = self.shell_proc.read_message()
        self.assertEqual(res["command"], "fail")
        self.assertEqual(res["id"], msg["id"])

        time.sleep(0.5)
        self.assertEqual(self.proc.poll(), 1)


if __name__ == '__main__':
    unittest.main()

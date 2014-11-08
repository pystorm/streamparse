from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import subprocess
import unittest
import time


_ROOT = os.path.dirname(os.path.realpath(__file__))
def here(*x):
    return os.path.join(_ROOT, *x)


def get_message(id=None, comp=None, stream=None, task=None, tuple=None):
    return {
        "id": "2285924946354050200" if id is None else id,
        "comp": "word-spout" if comp is None else comp,
        "stream": "default" if stream is None else stream,
        "task": 0 if task is None else task,
        "tuple": ["snow white and the seven dwarfs", "field2", 3, 4.252] if \
                 tuple is None else tuple,
    }


class ShellComponentTestCaseMixin(object):
    """Base test case for Spouts/Bolts. Takes care of creating a subprocess
    as well as the initial handshake to the component.
    """

    component = None

    @classmethod
    def setUpClass(cls):
        args = ["python", here(cls.component)]
        cls.proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        print("Waiting for {} subprocess to start."
              .format(cls.__name__))
        time.sleep(1)  # time for the subprocess to start
        if cls.proc.poll() is not None:
            raise Exception("Could not create subprocess.\n{}"
                            .format(cls.proc.stderr.read().decode('utf-8')))
        print("Done.")
        cls.shell_proc = ShellProcess(cls.proc.stdout, cls.proc.stdin)

    def test_0_initial_handshake(self):
        msg = {
            "conf": {},
            "context": {},
            "pidDir": here()
        }
        self.shell_proc.write_message(msg)
        res = self.shell_proc.read_message()

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("pid"), self.proc.pid)
        pid = str(res["pid"])
        self.assertTrue(os.path.exists(here(pid)))
        self.assertTrue(os.path.isfile(here(pid)))

        res = self.shell_proc.read_message()
        # logging is not configured msg
        self.assertEqual(res["command"], "log")

    @classmethod
    def tearDownClass(cls):
        os.remove(here(str(cls.proc.pid)))
        if cls.proc.poll() is None:
            cls.proc.kill()


class ShellProcess(object):
    """Immitation of https://github.com/apache/incubator-storm/blob/0.8.2/src/jvm/backtype/storm/utils/ShellProcess.java
    """
    DEFAULT_STREAM_ID = 1

    def __init__(self, in_buf, out_buf):
        self.in_buf = in_buf
        self.out_buf = out_buf

    def write_message(self, msg):
        self.write_string(json.dumps(msg))

    def write_string(self, string):
        self.out_buf.write("{}\nend\n".format(string).encode('utf-8'))
        self.out_buf.flush()

    def read_message(self):
        return json.loads(self.read_string())

    def read_string(self):
        res = ""
        while True:
            in_line = self.in_buf.readline().decode('utf-8')[0:-1]
            if not in_line:
                raise Exception("Pipe to subprocess seems to be broken!")

            if in_line == "end":
                break
            if len(res) != 0:
                res = "{}\n".format(res)
            res = "{}{}".format(res, in_line)

        return res

    def query_subprocess(self, query):
        actions = []
        self.write_message(query)

        while True:
            action = self.read_message()
            actions.append(action)
            if action.get("command") == "sync":
                return actions
            elif action.get("command") == "emit":
                stream = action.get("stream") or self.DEFAULT_STREAM_ID
                task = action.get("task")
                need_task_ids = action.get("need_task_ids") or True
                if task is None:
                    if need_task_ids:
                        self.write_message([1, 2])  # made up task IDs

import json


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
        self.out_buf.write("{}\nend\n".format(string))
        self.out_buf.flush()

    def read_message(self):
        return json.loads(self.read_string())

    def read_string(self):
        res = ""
        while True:
            in_line = self.in_buf.readline()[0:-1]
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
                need_task_ids = action.get("need_task_ids")
                if task is None:
                    if need_task_ids is None and need_task_ids == True:
                        self.write_message([1, 2])  # made up task IDs


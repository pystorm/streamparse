import logging
import unittest

from streamparse.cli import common
from streamparse.dsl import Grouping, Stream, Topology
from streamparse.storm import (
    Bolt,
    Component,
    JavaBolt,
    JavaSpout,
    ShellBolt,
    ShellSpout,
    Spout,
)

log = logging.getLogger(__name__)


class WordSpout(Spout):
    outputs = ["word"]


class WordCountBolt(Bolt):
    outputs = ["word", "count"]


class MultiStreamWordCountBolt(Bolt):
    outputs = [
        Stream(fields=["word", "count"]),
        Stream(fields=["all_word_count"], name="sum"),
    ]


class DatabaseDumperBolt(Bolt):
    outputs = []


class CliCommonTests(unittest.TestCase):
    """Tests streamparse/cli/common"""

    maxDiff = 1000

    def test_resolve_options(self):
        """Ensure that CLI > topo settings > config.json"""

        class WordCount(Topology):
            config = {"virtualenv_flags": "-p /path/to/python3"}
            word_spout = WordSpout.spec()
            word_bolt = WordCountBolt.spec(inputs=[word_spout])

        cli_options = {}
        env_config = {
            "user": "username",
            "nimbus": "nimbus.example.com:6627",
            "log": {"level": "info"},
            "virtualenv_root": "/path/to/virtualenvs",
            "virtualenv_flags": "/path/to/python2",
            "ui.port": 8081,
            "options": {
                "supervisor.worker.timeout.secs": 600,
                "topology.message.timeout.secs": 60,
                "topology.max.spout.pending": 500,
            },
        }

        options = common.resolve_options(
            cli_options, env_config, WordCount, "word_count", local_only=True
        )

        self.assertEqual(options["supervisor.worker.timeout.secs"], 600)
        self.assertEqual(options["virtualenv_flags"], "-p /path/to/python3")

        cli_options = {"virtualenv_flags": "-p /path/to/python3.6"}
        options = common.resolve_options(
            cli_options, env_config, WordCount, "word_count", local_only=True
        )

        self.assertEqual(options["supervisor.worker.timeout.secs"], 600)
        self.assertEqual(options["virtualenv_flags"], "-p /path/to/python3.6")

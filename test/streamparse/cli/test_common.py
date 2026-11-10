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

    def test_option_without_equals_is_usage_error(self):
        """`-o topology.debug` (missing =value) must exit 2, not traceback."""
        import argparse
        import contextlib
        import io

        parser = argparse.ArgumentParser(prog="sparse")
        common.add_options(parser)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                parser.parse_args(["-o", "topology.debug"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("KEY=VALUE", stderr.getvalue())

    def test_option_with_equals_still_parses(self):
        """`-o topology.debug=true` keeps working after the validation."""
        import argparse

        parser = argparse.ArgumentParser(prog="sparse")
        common.add_options(parser)
        ns = parser.parse_args(["-o", "topology.debug=true"])
        self.assertEqual(ns.options, {"topology.debug": True})

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

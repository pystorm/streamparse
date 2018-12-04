from __future__ import absolute_import, unicode_literals

import argparse
import unittest

from streamparse.cli.worker_uptime import subparser_hook

from nose.tools import ok_


class WorkerUptimeTestCase(unittest.TestCase):
    def test_subparser_hook(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser_hook(subparsers)

        subcommands = parser._optionals._actions[1].choices.keys()
        ok_("worker_uptime" in subcommands)


if __name__ == "__main__":
    unittest.main()

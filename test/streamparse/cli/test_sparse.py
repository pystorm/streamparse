from __future__ import absolute_import, unicode_literals

import argparse
import unittest

from streamparse.cli import sparse

from nose.tools import ok_


class SparseTestCase(unittest.TestCase):
    def test_load_subparsers(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        sparse.load_subparsers(subparsers)
        # grab subcommands from subparsers
        subcommands = parser._optionals._actions[1].choices.keys()
        # we know quickstart will be a subcommand test others as needed
        ok_("quickstart" in subcommands)


if __name__ == "__main__":
    unittest.main()

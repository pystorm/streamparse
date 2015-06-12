from   __future__ import print_function, unicode_literals
from   nose.tools import ok_
import argparse
import unittest
import streamparse.bin.sparse as sparse


class SparseTestCase(unittest.TestCase):
    def test_load_subparsers(self):
        parser     = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        sparse.load_suparsers(subparsers)
        # grab subcommands from subparsers
        subcommands = parser._optionals._actions[1].choices.keys()
        # we know quickstart will be a subcommand test others as needed
        ok_('quickstart' in subcommands)

if __name__ == '__main__':
    unittest.main()

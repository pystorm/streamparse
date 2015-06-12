from   __future__ import absolute_import, print_function, unicode_literals
from   nose.tools import ok_
import os
import argparse
import unittest
import streamparse.bin.sparse as sparse


class SparseTestCase(unittest.TestCase):
    def test_load_subparsers(self):
        parser     = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        imp_path   = os.path.dirname(os.path.realpath(sparse.__file__))
        sparse.load_suparsers(imp_path, subparsers)
        # grab subcommands from subparsers
        subcommands = parser._optionals._actions[1].choices.keys()
        # we know quickstart will be a subcommand test others as needed
        ok_('quickstart' in subcommands)

if __name__ == '__main__':
    unittest.main()

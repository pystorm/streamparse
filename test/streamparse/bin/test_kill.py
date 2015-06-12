from   __future__ import absolute_import, print_function, unicode_literals
from   nose.tools import ok_
from   streamparse.bin.kill import subparser_hook
import argparse
import unittest



class KillTestCase(unittest.TestCase):
    def test_subparser_hook(self):
        parser     = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser_hook(subparsers)

        subcommands = parser._optionals._actions[1].choices.keys()
        ok_('kill' in subcommands)

if __name__ == '__main__':
    unittest.main()

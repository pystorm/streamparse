from __future__ import absolute_import, unicode_literals

import argparse
import unittest

from nose.tools import ok_
try:
	from unittest.mock import patch
except ImportError:
	from mock import patch

from streamparse.cli.run import main, subparser_hook


class RunTestCase(unittest.TestCase):

    def test_subparser_hook(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser_hook(subparsers)

        subcommands = parser._optionals._actions[1].choices.keys()
        ok_('run' in subcommands)


    @patch('streamparse.cli.run.run_local_topology', autospec=True)
    def test_main_args_passed(self, run_local_mock):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser_hook(subparsers)

        args = parser.parse_args('run -e my_env -n my_topo --ackers 1'.split())

        main(args)
        run_local_mock.assert_called_with(name='my_topo',
                                          options={'topology.acker.executors': 1},
                                          env_name='my_env',
                                          time=0)


if __name__ == '__main__':
    unittest.main()

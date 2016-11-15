"""
This module provides the base sparse command and a load hook for dynamically
adding other subcommands.  The "load_suparsers" function searches for modules
in the streamparse/bin directory that have a "subparser_hook" method. The
"subparser_hook" accepts a the sparse subparsers object and adds it's
subparser as needed.
"""

from __future__ import absolute_import

import argparse
import importlib
import os
import pkgutil
import sys

from ..util import die
from ..version import __version__


def load_subparsers(subparsers):
    """
    searches modules in streamparse/bin for a 'subparser_hook' method and calls
    the 'subparser_hook' method on the sparse subparsers object.
    """
    for _, mod_name, is_pkg in pkgutil.iter_modules([os.path.dirname(__file__)]):
        if not is_pkg and mod_name not in sys.modules:
            module = importlib.import_module('streamparse.cli.{}'.format(mod_name))
            # check for the subparser hook
            if hasattr(module, 'subparser_hook'):
                module.subparser_hook(subparsers)


def main():
    """main entry point for sparse"""
    parser = argparse.ArgumentParser(description='Utilities for managing Storm'
                                                 '/streamparse topologies.',
                                     epilog='sparse provides a front-end to '
                                            'streamparse, a framework for '
                                            'creating Python projects for '
                                            'running, debugging, and '
                                            'submitting computation topologies '
                                            'against real-time streams, using '
                                            'Apache Storm. It requires java and'
                                            ' lein (Clojure build tool) to be '
                                            'on your $PATH, and uses lein and '
                                            'Clojure under the hood for JVM/'
                                            'Thrift interop.')
    subparsers = parser.add_subparsers(title='sub-commands')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    load_subparsers(subparsers)

    def _help_command(args):
        """Print help information about other commands.

        Does the same thing as adding --help flag to sub-command calls.
        """
        subparsers.choices[args.sub_command].print_help()
        sys.exit(1)

    help_parser = subparsers.add_parser('help',
                                        description=_help_command.__doc__,
                                        help=_help_command.__doc__.splitlines()[0])
    help_parser.add_argument('sub_command',
                             help='The command to provide help for.',
                             choices=sorted(subparsers.choices.keys()))
    help_parser.set_defaults(func=_help_command)
    args = parser.parse_args()

    if os.getuid() == 0 and not os.getenv('LEIN_ROOT'):
        die('Because streamparse relies on Leiningen, you cannot run '
            'streamparse as root without the LEIN_ROOT environment variable '
            'set. Otherwise, Leiningen would hang indefinitely under-the-hood '
            'waiting for user input.')

    # http://grokbase.com/t/python/python-bugs-list/12arsq9ayf/issue16308-undocumented-behaviour-change-in-argparse-from-3-2-3-to-3-3-0
    if hasattr(args, 'func'):
        args.func(args)
    # python3.3+ argparse changes
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()

"""
Tail logs for specified Storm topology.
"""

from __future__ import absolute_import, print_function

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter

from streamparse.bin.common import add_environment, add_name
from streamparse.ext.invoke import tail_topology


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('tail',
                                      formatter_class=DefaultsHelpFormatter,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)
    add_name(subparser)
    subparser.add_argument('--pattern',
                           help='Pattern of files to tail with "tail -f"')


def main(args):
    """ Tail logs for specified Storm topology. """
    tail_topology(args.name, args.environment, args.pattern)

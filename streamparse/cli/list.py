"""
List the currently running Storm topologies.
"""

from __future__ import absolute_import

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter

from streamparse.cli.common import add_environment
from streamparse.ext.invoke import list_topologies


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('list',
                                      formatter_class=DefaultsHelpFormatter,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)


def main(args):
    """ List the currently running Storm topologies """
    list_topologies(env_name=args.environment)

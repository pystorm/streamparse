"""
Tail logs for specified Storm topology.
"""

from __future__ import absolute_import, print_function

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter

from .common import add_environment, add_name
from ..ext.fabric import activate_env, tail_logs
from ..ext.util import get_topology_definition


def tail_topology(topology_name=None, env_name=None, pattern=None):
    get_topology_definition(topology_name)
    activate_env(env_name)
    tail_logs(topology_name, pattern)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('tail',
                                      formatter_class=DefaultsHelpFormatter,
                                      description=__doc__,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)
    add_name(subparser)
    subparser.add_argument('--pattern',
                           help='Pattern of files to tail with "tail -f"')


def main(args):
    """ Tail logs for specified Storm topology. """
    tail_topology(args.name, args.environment, args.pattern)

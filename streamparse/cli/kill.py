"""
Kill the specified Storm topology.
"""

from __future__ import absolute_import

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter

from streamparse.cli.common import add_environment, add_name, add_wait
from streamparse.ext.invoke import kill_topology


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('kill',
                                      formatter_class=DefaultsHelpFormatter,
                                      description=__doc__,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)
    add_name(subparser)
    add_wait(subparser)

def main(args):
    """ Kill the specified Storm topology """
    kill_topology(topology_name=args.name, env_name=args.environment,
                  wait=args.wait)

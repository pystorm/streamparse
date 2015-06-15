"""
Display uptime for workers in running Storm topologies.
"""

from __future__ import absolute_import, print_function

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter
from pkg_resources import parse_version

from streamparse.cli.common import add_environment
from streamparse.ext.invoke import display_worker_uptime, storm_lib_version


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('worker-uptime',
                                      formatter_class=DefaultsHelpFormatter,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)


def main(args):
    """ Display uptime for workers in running Storm topologies. """
    storm_version = storm_lib_version()
    if storm_version >= parse_version('0.9.2-incubating'):
        display_worker_uptime(args.environment)
    else:
        print("ERROR: Storm {0} does not support this command."
              .format(storm_version))

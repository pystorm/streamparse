"""
Display stats about running Storm topologies.
"""

from __future__ import absolute_import, print_function

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter
from pkg_resources import parse_version

from streamparse.cli.common import add_environment
from streamparse.ext.invoke import display_stats, storm_lib_version


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('stats',
                                      formatter_class=DefaultsHelpFormatter,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    subparser.add_argument('--all',
                           action='store_true',
                           help='All available stats.')
    subparser.add_argument('-c', '--components',
                           help='Topology component (bolt/spout) name as '
                                'specified in Clojure topology specification')
    add_environment(subparser)


def main(args):
    """ Display stats about running Storm topologies. """
    storm_version = storm_lib_version()
    if storm_version >= parse_version('0.9.2-incubating'):
        display_stats(args.environment, args.name, args.component, args.all)
    else:
        print("ERROR: Storm {0} does not support this command."
              .format(storm_version))

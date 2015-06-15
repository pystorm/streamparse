"""
Create a graphviz visualization of the specified topology.
Does not currently work!
"""

from __future__ import absolute_import, print_function

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter

from streamparse.cli.common import add_name
from streamparse.ext.invoke import visualize_topology


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('visualize',
                                      formatter_class=DefaultsHelpFormatter,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    subparser.add_argument('-f', '--flip',
                           action='store_true',
                           help='Flip the visualization to be horizontal.')
    add_name(subparser)

def main(args):
    """ Create a graphviz visualization of the specified topology.   """
    visualize_topology(args.name)

"""
Create a graphviz visualization of the specified topology.
Does not currently work!
"""

from __future__ import absolute_import, print_function

import sys
from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter

from invoke import run

from .common import add_name
from ..ext.util import get_topology_definition


def visualize_topology(name=None, flip=False):
    name, topology_file = get_topology_definition(name)
    print("Visualizing {} topology...".format(name))
    sys.stdout.flush()
    cmd = ["lein",
           "run -m streamparse.commands.visualize/-main",
           topology_file]
    if flip:
        cmd.append("-f")
    full_cmd = " ".join(cmd)
    print("Running lein command to visualize topology:")
    print(full_cmd)
    sys.stdout.flush()
    run(full_cmd)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('visualize',
                                      formatter_class=DefaultsHelpFormatter,
                                      description=__doc__,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    subparser.add_argument('-f', '--flip',
                           action='store_true',
                           help='Flip the visualization to be horizontal.')
    add_name(subparser)

def main(args):
    """ Create a graphviz visualization of the specified topology.   """
    visualize_topology(args.name)

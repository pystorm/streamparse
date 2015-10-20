"""
Create a graphviz visualization of the specified topology.

Unfortunately, this does not currently work, because of packaging difficulities
with Clojure.  In version 2.0, this will replaced with a pure-Python approach to
visualizing topologies.  See GitHub issue #22.
"""

from __future__ import absolute_import, print_function

import sys

from invoke import run

from .common import add_name
from ..util import get_topology_definition


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
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    subparser.add_argument('-f', '--flip',
                           action='store_true',
                           help='Flip the visualization to be horizontal.')
    add_name(subparser)

def main(args):
    """ Create a graphviz visualization of a topology. """
    visualize_topology(args.name)

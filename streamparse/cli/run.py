"""
Run a local Storm topology.
"""

from __future__ import absolute_import

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter

from streamparse.cli.common import (add_ackers, add_debug, add_environment,
                                    add_name, add_options, add_par, add_workers)
from streamparse.ext.invoke import run_local_topology


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('run',
                                      formatter_class=DefaultsHelpFormatter,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    add_ackers(subparser)
    add_debug(subparser)
    add_environment(subparser)
    add_name(subparser)
    add_options(subparser)
    add_par(subparser)
    subparser.add_argument('-t', '--time',
                           default=0,
                           type=int,
                           help='Time (in seconds) to keep local cluster '
                                'running. If time <= 0, run indefinitely.')
    add_workers(subparser)


def main(args):
    """ Run the local topology with the given arguments """
    run_local_topology(name=args.name, time=args.time, workers=args.workers,
                       ackers=args.ackers, options=args.options,
                       debug=args.debug)

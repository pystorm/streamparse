"""
Submit a Storm topology to Nimbus.
"""

from __future__ import absolute_import

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter

from streamparse.bin.common import (add_ackers, add_debug, add_environment,
                                    add_name, add_options, add_par, add_wait,
                                    add_workers)
from streamparse.ext.invoke import submit_topology


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('submit',
                                      formatter_class=DefaultsHelpFormatter,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    add_ackers(subparser)
    add_debug(subparser)
    add_environment(subparser)
    subparser.add_argument('-f', '--force',
                           action='store_true',
                           help='Force a topology to submit by killing any '
                                'currently running topologies with the same '
                                'name.')
    add_name(subparser)
    add_options(subparser)
    add_par(subparser)
    subparser.add_argument('-t', '--time',
                           default=0,
                           type=int,
                           help='Time (in seconds) to keep local cluster '
                                'running. If time <= 0, run indefinitely.')
    add_wait(subparser)
    add_workers(subparser)


def main(args):
    """ Submit a Storm topology to Nimbus. """
    submit_topology(name=args.name, env_name=args.environment,
                    workers=args.workers, ackers=args.ackers,
                    options=args.options, force=args.force, debug=args.debug,
                    wait=args.wait)

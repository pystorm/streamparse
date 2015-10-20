"""
Run a local Storm topology.
"""

from __future__ import absolute_import, print_function

import os
import sys

from invoke import run

from .common import (add_ackers, add_debug, add_environment, add_name,
                     add_options, add_par, add_workers, resolve_ackers_workers)
from ..util import prepare_topology, get_topology_definition


def run_local_topology(name=None, time=0, workers=2, ackers=2, options=None,
                       debug=False):
    """Run a topology locally using Storm's LocalCluster class."""
    prepare_topology()

    name, topology_file = get_topology_definition(name)
    print("Running {} topology...".format(name))
    sys.stdout.flush()
    cmd = ["lein",
           "run -m streamparse.commands.run/-main",
           topology_file]
    cmd.append("-t {}".format(time))
    if debug:
        cmd.append("--debug")
    cmd.append("--option 'topology.workers={}'".format(workers))
    cmd.append("--option 'topology.acker.executors={}'".format(ackers))

    # Python logging settings
    if not os.path.isdir("logs"):
        os.makedirs("logs")
    log_path = os.path.join(os.getcwd(), "logs")
    print("Routing Python logging to {}.".format(log_path))
    sys.stdout.flush()
    cmd.append("--option 'streamparse.log.path=\"{}\"'"
               .format(log_path))
    cmd.append("--option 'streamparse.log.level=\"debug\"'")

    if options is None:
        options = []
    for option in options:
        cmd.append('--option {}'.format(option))
    full_cmd = " ".join(cmd)
    print("Running lein command to run local cluster:")
    print(full_cmd)
    sys.stdout.flush()
    run(full_cmd)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('run',
                                      description=__doc__,
                                      help=main.__doc__)
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
                                'running. If time <= 0, run indefinitely. '
                                '(default: %(default)s)')
    add_workers(subparser)


def main(args):
    """ Run the local topology with the given arguments """
    resolve_ackers_workers(args)
    run_local_topology(name=args.name, time=args.time, workers=args.workers,
                       ackers=args.ackers, options=args.options,
                       debug=args.debug)

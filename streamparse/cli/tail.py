"""
Tail the specified log files with "tail -f".
"""

from __future__ import absolute_import, print_function

from fabric.api import env, execute, parallel, run, task

from .common import add_environment, add_name, add_pattern
from ..util import (activate_env, get_env_config, get_logfiles_cmd,
                    get_topology_definition)


@parallel
def _tail_logs(topology_name=None, pattern=None):
    """
    Actual task to run tail -f on all servers in parallel.
    """
    ls_cmd = get_logfiles_cmd(topology_name=topology_name, pattern=pattern)
    tail_pipe = " | xargs tail"
    run(ls_cmd + tail_pipe)


def tail_topology(topology_name=None, env_name=None, pattern=None):
    """Follow (tail -f) the log files on remote Storm workers.

    Will use the `log_path` and `workers` properties from config.json.
    """
    topology_name = get_topology_definition(topology_name)[0]
    activate_env(env_name)
    execute(_tail_logs, topology_name, pattern, hosts=env.storm_workers)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('tail',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)
    add_name(subparser)
    add_pattern(subparser)


def main(args):
    """ Tail logs for specified Storm topology. """
    tail_topology(topology_name=args.name, env_name=args.environment,
                  pattern=args.pattern)

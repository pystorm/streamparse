"""
Remove all logs from Storm workers for the specified Storm topology.
"""

from __future__ import absolute_import, print_function

from fabric.api import env, execute, parallel, sudo

from .common import add_environment, add_name, add_pattern
from ..util import activate_env, get_topology_definition, get_logfiles_cmd


@parallel
def _remove_logs(topology_name, pattern, remove_worker_logs):
    """
    Actual task to remove logs on all servers in parallel.
    """
    ls_cmd = get_logfiles_cmd(topology_name=topology_name, pattern=pattern,
                              include_worker_logs=remove_worker_logs)
    rm_pipe = " | xargs rm"
    sudo(ls_cmd + rm_pipe, warn_only=True)


def remove_logs(topology_name=None, env_name=None, pattern=None,
                remove_worker_logs=False):
    """Remove all Python logs on Storm workers in the log.path directory."""
    topology_name = get_topology_definition(topology_name)[0]
    activate_env(env_name)
    execute(_remove_logs, topology_name, pattern, remove_worker_logs,
            hosts=env.storm_workers)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('remove_logs',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)
    add_name(subparser)
    add_pattern(subparser)
    subparser.add_argument('-u', '--user',
                           help="User argument to sudo when deleting logs.")
    subparser.add_argument('-w', '--remove_worker_logs',
                           help='Remove not only topology-specific logs, but '
                                'also worker logs that may be shared between '
                                'topologies.',
                           action='store_true')

def main(args):
    """ Remove logs from Storm workers. """
    remove_logs(topology_name=args.name, env_name=args.environment,
                pattern=args.pattern,
                remove_worker_logs=args.remove_worker_logs)

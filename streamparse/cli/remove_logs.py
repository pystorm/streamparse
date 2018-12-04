"""
Remove all logs from Storm workers for the specified Storm topology.
"""

from __future__ import absolute_import, print_function

from fabric.api import env, execute, parallel, run, sudo
from pkg_resources import parse_version

from .common import (
    add_config,
    add_environment,
    add_name,
    add_override_name,
    add_pattern,
    add_pool_size,
)
from ..util import (
    activate_env,
    get_env_config,
    get_topology_definition,
    get_logfiles_cmd,
    get_nimbus_client,
    nimbus_storm_version,
    ssh_tunnel,
)


@parallel
def _remove_logs(
    topology_name, pattern, remove_worker_logs, user, is_old_storm, remove_all_artifacts
):
    """
    Actual task to remove logs on all servers in parallel.
    """
    ls_cmd = get_logfiles_cmd(
        topology_name=topology_name,
        pattern=pattern,
        include_worker_logs=remove_worker_logs,
        include_all_artifacts=remove_all_artifacts,
    )
    rm_pipe = " | xargs rm -f"
    if user == env.user:
        run(ls_cmd + rm_pipe, warn_only=True)
    else:
        sudo(ls_cmd + rm_pipe, warn_only=True, user=user)


def remove_logs(
    topology_name=None,
    env_name=None,
    pattern=None,
    remove_worker_logs=False,
    user="root",
    override_name=None,
    remove_all_artifacts=False,
    options=None,
    config_file=None,
):
    """Remove all Python logs on Storm workers in the log.path directory."""
    if override_name is not None:
        topology_name = override_name
    else:
        topology_name = get_topology_definition(topology_name, config_file=config_file)[
            0
        ]
    env_name, env_config = get_env_config(env_name, config_file=config_file)
    with ssh_tunnel(env_config) as (host, port):
        nimbus_client = get_nimbus_client(env_config, host=host, port=port)
        is_old_storm = nimbus_storm_version(nimbus_client) < parse_version("1.0")
    activate_env(env_name, options=options)
    execute(
        _remove_logs,
        topology_name,
        pattern,
        remove_worker_logs,
        user,
        is_old_storm,
        remove_all_artifacts,
        hosts=env.storm_workers,
    )


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser(
        "remove_logs", description=__doc__, help=main.__doc__
    )
    subparser.set_defaults(func=main)
    subparser.add_argument(
        "-A",
        "--remove_all_artifacts",
        help="Remove not only topology-specific logs, but "
        "also any other files for the topology in its "
        "workers-artifacts subdirectories.",
        action="store_true",
    )
    add_config(subparser)
    add_environment(subparser)
    add_name(subparser)
    add_override_name(subparser)
    add_pattern(subparser)
    add_pool_size(subparser)
    # Not using add_user because we need -u for backward compatibility
    subparser.add_argument(
        "-u", "--user", help="User argument to sudo when deleting logs.", default="root"
    )
    subparser.add_argument(
        "-w",
        "--remove_worker_logs",
        help="Remove not only topology-specific logs, but "
        "also worker logs that may be shared between "
        "topologies.",
        action="store_true",
    )


def main(args):
    """ Remove logs from Storm workers. """
    env.pool_size = args.pool_size
    remove_logs(
        topology_name=args.name,
        env_name=args.environment,
        pattern=args.pattern,
        remove_worker_logs=args.remove_worker_logs,
        user=args.user,
        override_name=args.override_name,
        remove_all_artifacts=args.remove_all_artifacts,
        config_file=args.config,
    )

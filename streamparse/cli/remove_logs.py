"""
Remove all logs from Storm workers for the specified Storm topology.
"""

from __future__ import absolute_import, print_function

try:
    import simplejson as json
except ImportError:
    import json
from pkg_resources import parse_version
from pssh.clients.native import ParallelSSHClient

from .common import (
    add_config,
    add_environment,
    add_name,
    add_options,
    add_override_name,
    add_pattern,
    add_pool_size,
    resolve_options,
)
from ..util import (
    get_config_dict,
    get_env_config,
    get_logfiles_cmd,
    get_nimbus_client,
    get_topology_definition,
    get_topology_from_file,
    nimbus_storm_version,
    print_ssh_output,
    ssh_tunnel,
)


def _remove_logs(
    topology_name,
    pattern,
    remove_worker_logs,
    user,
    env_user,
    is_old_storm,
    remove_all_artifacts,
    log_path,
    hosts,
    pool_size,
):
    """
    Actual task to remove logs on all servers in parallel.
    """
    ls_cmd = get_logfiles_cmd(
        topology_name=topology_name,
        pattern=pattern,
        include_worker_logs=remove_worker_logs,
        include_all_artifacts=remove_all_artifacts,
        log_path=log_path,
    )
    rm_pipe = " | xargs rm -f"
    ssh_client = ParallelSSHClient(hosts, pool_size=pool_size)
    run_kwargs = {} if user == env_user else {"user": user, "sudo": True}
    output = ssh_client.run_command(ls_cmd + rm_pipe, **run_kwargs)

    ssh_client.join(output)
    print_ssh_output(output)


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
    pool_size=10,
):
    """Remove all Python logs on Storm workers in the log.path directory."""
    topology_name, topology_file = get_topology_definition(
        topology_name, config_file=config_file
    )
    topology_class = get_topology_from_file(topology_file)
    if override_name is not None:
        topology_name = override_name
    else:
        topology_name = get_topology_definition(topology_name, config_file=config_file)[
            0
        ]
    env_name, env_config = get_env_config(env_name, config_file=config_file)

    options = resolve_options(options, env_config, topology_class, topology_name)
    env_dict = get_config_dict(env_name, options=options, config_file=config_file)
    log_path = env_dict["log_path"]

    with ssh_tunnel(env_config) as (host, port):
        nimbus_client = get_nimbus_client(env_config, host=host, port=port)
        is_old_storm = nimbus_storm_version(nimbus_client) < parse_version("1.0")

    _remove_logs(
        topology_name,
        pattern,
        remove_worker_logs,
        user,
        env_dict["user"],
        is_old_storm,
        remove_all_artifacts,
        log_path,
        env_dict["storm_workers"],
        pool_size,
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
    remove_logs(
        topology_name=args.name,
        env_name=args.environment,
        pattern=args.pattern,
        remove_worker_logs=args.remove_worker_logs,
        user=args.user,
        override_name=args.override_name,
        remove_all_artifacts=args.remove_all_artifacts,
        config_file=args.config,
        pool_size=args.pool_size,
    )

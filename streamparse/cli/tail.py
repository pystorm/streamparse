"""
Tail the specified log files.
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
    add_override_name,
    add_options,
    add_pattern,
    add_pool_size,
    resolve_options,
)
from ..util import (
    get_config_dict,
    get_env_config,
    get_logfiles_cmd,
    get_topology_definition,
    get_topology_from_file,
    get_nimbus_client,
    nimbus_storm_version,
    print_ssh_output,
    ssh_tunnel,
)


def _tail_logs(
    topology_name, pattern, follow, num_lines, is_old_storm, log_path, hosts, pool_size
):
    """
    Actual task to run tail on all servers in parallel.
    """
    ls_cmd = get_logfiles_cmd(
        topology_name=topology_name,
        pattern=pattern,
        is_old_storm=is_old_storm,
        log_path=log_path,
    )
    tail_pipe = " | xargs tail -n {}".format(num_lines)
    if follow:
        tail_pipe += " -f"

    ssh_client = ParallelSSHClient(hosts, pool_size=pool_size)
    output = ssh_client.run_command(ls_cmd + tail_pipe)
    print_ssh_output(output)


def tail_topology(
    topology_name=None,
    env_name=None,
    pattern=None,
    follow=False,
    num_lines=10,
    override_name=None,
    config_file=None,
    pool_size=10,
    options=None,
):
    """Follow (tail -f) the log files on remote Storm workers.

    Will use the `log_path` and `workers` properties from config.json.
    """
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

    options = resolve_options(options, env_config, topology_class, override_name)
    env_dict = get_config_dict(env_name, options=options, config_file=config_file)
    log_path = env_dict["log_path"]
    if log_path is None:
        raise ValueError(
            "Cannot find log files if you do not set `log_path` "
            "or the `path` key in the `log` dict for your "
            "environment in your config.json."
        )

    with ssh_tunnel(env_config) as (host, port):
        nimbus_client = get_nimbus_client(env_config, host=host, port=port)
        is_old_storm = nimbus_storm_version(nimbus_client) < parse_version("1.0")

    print("Tailing logs...")
    _tail_logs(
        topology_name,
        pattern,
        follow,
        num_lines,
        is_old_storm,
        log_path,
        options["storm.workers.list"],
        pool_size,
    )


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser("tail", description=__doc__, help=main.__doc__)
    subparser.set_defaults(func=main)
    add_config(subparser)
    add_environment(subparser)
    subparser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Keep files open and append output as they "
        'grow.  This is the same as "-f" parameter for '
        "the tail command that will be executed on the "
        "Storm workers.",
    )
    subparser.add_argument(
        "-l",
        "--num_lines",
        default=10,
        help="tail outputs the last NUM_LINES lines of the "
        "logs. (default: %(default)s)",
    )
    add_name(subparser)
    add_options(subparser)
    add_override_name(subparser)
    add_pool_size(subparser)
    add_pattern(subparser)


def main(args):
    """ Tail logs for specified Storm topology. """
    tail_topology(
        topology_name=args.name,
        env_name=args.environment,
        pattern=args.pattern,
        follow=args.follow,
        num_lines=args.num_lines,
        override_name=args.override_name,
        config_file=args.config,
        options=args.options,
    )

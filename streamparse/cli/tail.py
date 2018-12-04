"""
Tail the specified log files.
"""

from __future__ import absolute_import, print_function

from fabric.api import env, execute, parallel, run
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
    get_logfiles_cmd,
    get_topology_definition,
    get_nimbus_client,
    nimbus_storm_version,
    ssh_tunnel,
)


@parallel
def _tail_logs(topology_name, pattern, follow, num_lines, is_old_storm):
    """
    Actual task to run tail on all servers in parallel.
    """
    ls_cmd = get_logfiles_cmd(
        topology_name=topology_name, pattern=pattern, is_old_storm=is_old_storm
    )
    tail_pipe = " | xargs tail -n {}".format(num_lines)
    if follow:
        tail_pipe += " -f"
    run(ls_cmd + tail_pipe)


def tail_topology(
    topology_name=None,
    env_name=None,
    pattern=None,
    follow=False,
    num_lines=10,
    override_name=None,
    config_file=None,
):
    """Follow (tail -f) the log files on remote Storm workers.

    Will use the `log_path` and `workers` properties from config.json.
    """
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
    activate_env(env_name)
    execute(
        _tail_logs,
        topology_name,
        pattern,
        follow,
        num_lines,
        is_old_storm,
        hosts=env.storm_workers,
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
    add_override_name(subparser)
    add_pool_size(subparser)
    add_pattern(subparser)


def main(args):
    """ Tail logs for specified Storm topology. """
    env.pool_size = args.pool_size
    tail_topology(
        topology_name=args.name,
        env_name=args.environment,
        pattern=args.pattern,
        follow=args.follow,
        num_lines=args.num_lines,
        override_name=args.override_name,
        config_file=args.config,
    )

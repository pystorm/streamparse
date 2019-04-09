"""
Remove all logs from Storm workers for the specified Storm topology.
"""

from fabric.api import env, execute, parallel

from .common import (
    add_config,
    add_environment,
    add_name,
    add_override_name,
    add_pattern,
    add_pool_size,
    add_user,
    resolve_options,
    warn_about_deprecated_user,
)
from ..util import (
    activate_env,
    get_env_config,
    get_topology_definition,
    get_topology_from_file,
    get_logfiles_cmd,
    run_cmd,
)


@parallel
def _remove_logs(
    topology_name, pattern, remove_worker_logs, user, remove_all_artifacts
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
    run_cmd(ls_cmd + rm_pipe, user, warn_only=True)


def remove_logs(
    topology_name=None,
    env_name=None,
    pattern=None,
    remove_worker_logs=False,
    user=None,
    override_name=None,
    remove_all_artifacts=False,
    options=None,
    config_file=None,
):
    """Remove all Python logs on Storm workers in the log.path directory."""
    warn_about_deprecated_user(user, "remove_logs")
    topology_name, topology_file = get_topology_definition(
        override_name or topology_name, config_file=config_file
    )
    topology_class = get_topology_from_file(topology_file)
    env_name, env_config = get_env_config(env_name, config_file=config_file)
    storm_options = resolve_options(options, env_config, topology_class, topology_name)
    activate_env(env_name, storm_options, config_file=config_file)
    execute(
        _remove_logs,
        topology_name,
        pattern,
        remove_worker_logs,
        # TODO: Remove "user" in next major version
        user or storm_options["sudo_user"],
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
    add_user(subparser, allow_short=True)
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
        options=args.options,
        override_name=args.override_name,
        remove_all_artifacts=args.remove_all_artifacts,
        config_file=args.config,
    )

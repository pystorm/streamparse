"""
List the currently running Storm topologies.
"""

from __future__ import absolute_import

from ..util import get_env_config, get_nimbus_client, print_stats_table, ssh_tunnel
from ..thrift import TopologySummary
from .common import add_config, add_environment, add_timeout


def _list_topologies(nimbus_client):
    """:returns: A list of running Storm topologies"""
    cluster_summary = nimbus_client.getClusterInfo()
    return cluster_summary.topologies


def list_topologies(env_name, timeout=None, config_file=None):
    """Prints out all running Storm topologies"""
    env_name, env_config = get_env_config(env_name, config_file=config_file)
    # Use ssh tunnel with Nimbus if use_ssh_for_nimbus is unspecified or True
    with ssh_tunnel(env_config) as (host, port):
        nimbus_client = get_nimbus_client(
            env_config, host=host, port=port, timeout=timeout
        )
        topologies = _list_topologies(nimbus_client)
    if not topologies:
        print("No topologies found.")
    else:
        columns = [field for field, default in TopologySummary.default_spec]
        # Find values that are the same for all topologies and list those
        # separately to prevent table from being too wide
        if len(topologies) > 1:
            identical_vals = dict(vars(topologies[0]))
            for topology in topologies:
                for column in columns:
                    if column in identical_vals:
                        cur_val = getattr(topology, column)
                        if cur_val != identical_vals[column]:
                            identical_vals.pop(column)
            if identical_vals:
                for key in identical_vals.keys():
                    columns.remove(key)
                print_stats_table(
                    "Values identical for all topologies",
                    identical_vals,
                    list(identical_vals.keys()),
                    "l",
                )

        print_stats_table("Topology-specific values", topologies, columns, "l")


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser("list", description=__doc__, help=main.__doc__)
    subparser.set_defaults(func=main)
    add_config(subparser)
    add_environment(subparser)
    add_timeout(subparser)


def main(args):
    """ List the currently running Storm topologies """
    list_topologies(args.environment, timeout=args.timeout, config_file=args.config)

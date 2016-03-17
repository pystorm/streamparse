"""
List the currently running Storm topologies.
"""

from __future__ import absolute_import

from ..util import (get_env_config, get_nimbus_client, print_stats_table,
                    ssh_tunnel)
from ..thrift import storm_thrift
from .common import add_environment


def _list_topologies(nimbus_client):
    """:returns: A list of running Storm topologies"""
    cluster_summary = nimbus_client.getClusterInfo()
    return cluster_summary.topologies


def list_topologies(env_name):
    """Prints out all running Storm topologies"""
    env_name, env_config = get_env_config(env_name)
    # Use ssh tunnel with Nimbus if use_ssh_for_nimbus is unspecified or True
    with ssh_tunnel(env_config) as (host, port):
        nimbus_client = get_nimbus_client(env_config, host=host, port=port)
        topologies = _list_topologies(nimbus_client)
    if not topologies:
        print('No topologies found.')
    else:
        columns = [field for field, default in
                   storm_thrift.TopologySummary.default_spec]
        print_stats_table('Topologies', topologies, columns, 'l')


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('list',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)


def main(args):
    """ List the currently running Storm topologies """
    list_topologies(args.environment)

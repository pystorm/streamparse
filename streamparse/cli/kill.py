"""
Kill the specified Storm topology.
"""

from __future__ import absolute_import

from ..thrift import storm_thrift
from ..util import (get_topology_definition, get_env_config, get_nimbus_client,
                    ssh_tunnel)
from .common import add_environment, add_name, add_wait


def _kill_topology(topology_name, nimbus_client, wait=None):
    kill_opts = storm_thrift.KillOptions(wait_secs=wait)
    nimbus_client.killTopologyWithOpts(name=topology_name, options=kill_opts)


def kill_topology(topology_name=None, env_name=None, wait=None):
    # For kill, we allow any topology name to be specified, because people
    # should be able to kill topologies not in their local branch
    if topology_name is None:
        topology_name = get_topology_definition(topology_name)[0]
    env_name, env_config = get_env_config(env_name)
    # Use ssh tunnel with Nimbus if use_ssh_for_nimbus is unspecified or True
    with ssh_tunnel(env_config) as (host, port):
        nimbus_client = get_nimbus_client(env_config, host=host, port=port)
        return _kill_topology(topology_name, nimbus_client, wait=wait)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('kill',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)
    add_name(subparser)
    add_wait(subparser)


def main(args):
    """ Kill the specified Storm topology """
    kill_topology(topology_name=args.name, env_name=args.environment,
                  wait=args.wait)

"""
Kill the specified Storm topology.
"""

from __future__ import absolute_import

from invoke import run

from ..contextmanagers import ssh_tunnel
from ..util import (get_topology_definition, get_env_config,
                    get_nimbus_for_env_config, is_ssh_for_nimbus)
from .common import add_environment, add_name, add_wait


def _kill_topology(topology_name, wait=None,
                   host=None, port=None,
                   run_args=None, run_kwargs=None):
    if run_args is None:
        run_args = []
    if run_kwargs is None:
        run_kwargs = {}
    run_kwargs['pty'] = True
    wait_arg = ("--wait {wait}".format(wait=wait)) if wait is not None else ""
    cmd = ("lein run -m streamparse.commands.kill_topology/-main"
           " {topology_name} {wait}").format(topology_name=topology_name,
                                             wait=wait_arg)
    if host:
        cmd += " --host " + host
    if port:
        cmd += " --port " + str(port)
    return run(cmd, *run_args, **run_kwargs)


def kill_topology(topology_name=None, env_name=None, wait=None):
    topology_name = get_topology_definition(topology_name)[0]
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    if is_ssh_for_nimbus(env_config):
        with ssh_tunnel(env_config.get("user"), host, 6627, port):
            return _kill_topology(topology_name, wait)
    return _kill_topology(topology_name, wait, host=host, port=port)


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

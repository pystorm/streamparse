"""
List the currently running Storm topologies.
"""

from __future__ import absolute_import

from invoke import run

from .common import add_environment
from ..util import (get_env_config, get_nimbus_for_env_config,
                        is_ssh_for_nimbus)
from ..contextmanagers import ssh_tunnel


def _list_topologies(host=None, port=None, run_args=None, run_kwargs=None):
    if run_args is None:
        run_args = []
    if run_kwargs is None:
        run_kwargs = {}
    run_kwargs['pty'] = True
    cmd = ["lein",
           "run -m streamparse.commands.list/-main"]
    if host:
        cmd.append("--host {}".format(host))
    if port:
        cmd.append("--port {}".format(port))
    return run(" ".join(cmd), *run_args, **run_kwargs)


def list_topologies(env_name):
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    if is_ssh_for_nimbus(env_config):
        with ssh_tunnel(env_config.get("user"), host, 6627, port):
            return _list_topologies()
    return _list_topologies(host=host, port=port)


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

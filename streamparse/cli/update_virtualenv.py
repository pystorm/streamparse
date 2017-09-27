"""
Create or update a virtualenv on the Storm workers.  This will be done
automatically upon submit, but this command is provided to help with testing
and debugging.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
from io import open

from gevent import joinall
from pssh.pssh2_client import ParallelSSHClient
from six import string_types

from .common import (
    add_config,
    add_environment,
    add_name,
    add_options,
    add_override_name,
    add_overwrite_virtualenv,
    add_pool_size,
    add_requirements,
    add_user,
    resolve_options,
)
from ..util import (
    die,
    get_config_dict,
    get_config,
    get_env_config,
    get_topology_definition,
    get_topology_from_file,
    print_ssh_output,
)


def _create_or_update_virtualenv(
    virtualenv_root,
    virtualenv_name,
    requirements_paths,
    hosts=None,
    virtualenv_flags=None,
    overwrite_virtualenv=False,
    user="root",
    env_user="root",
    pool_size=10,
):
    virtualenv_path = "/".join((virtualenv_root, virtualenv_name))
    ssh_client = ParallelSSHClient(hosts, pool_size=pool_size)
    virtualenv_exists_output = ssh_client.run_command(
        'if [ -d {} ]; then echo "present"; fi'.format(virtualenv_path)
    )

    if overwrite_virtualenv:
        run_kwargs = {} if user == env_user else {"user": user, "sudo": True}
        output = ssh_client.run_command(
            "rm -rf {}".format(virtualenv_path), **run_kwargs
        )
        ssh_client.join(output)
    else:
        hosts_without_virtualenv = []
        for host, host_output in virtualenv_exists_output.items():
            try:
                next(host_output.stdout)
            except StopIteration:
                if virtualenv_flags is None:
                    virtualenv_flags = ""
                hosts_without_virtualenv.append(host)
        ssh_client.hosts = hosts_without_virtualenv

    print("Creating virtualenvs as necessary...")
    output = ssh_client.run_command(
        "virtualenv {} {}".format(virtualenv_path, virtualenv_flags)
    )
    ssh_client.join(output)
    ssh_client.hosts = hosts

    if isinstance(requirements_paths, string_types):
        requirements_paths = [requirements_paths]

    for requirements_path in requirements_paths:
        output = ssh_client.run_command(
            "mktemp /tmp/streamparse_requirements-XXXXXXXXX.txt"
        )
        temp_req = next(output[hosts[0]].stdout)
        greenlets = ssh_client.copy_file(requirements_path, temp_req)
        joinall(greenlets)

        virtualenv_activate = "source {}".format(
            os.path.join(virtualenv_path, "bin/activate")
        )
        pip_upgrade = "pip install --upgrade 'pip>=9.0'"
        pip_requirements_install = (
            "pip install -r {} --exists-action w --upgrade --upgrade-strategy "
            "only-if-needed".format(temp_req)
        )

        output = ssh_client.run_command(
            "{} && {} && {}".format(
                virtualenv_activate, pip_upgrade, pip_requirements_install
            )
        )
        ssh_client.join(output)
        print_ssh_output(output)
        ssh_client.join(output)
        output = ssh_client.run_command("rm {}".format(temp_req))
        ssh_client.join(output)
        print_ssh_output(output)

    print("Updated virtualenvs on all Storm workers.")


def create_or_update_virtualenvs(
    env_name,
    topology_name,
    options,
    virtualenv_name=None,
    requirements_paths=None,
    config_file=None,
    overwrite_virtualenv=False,
    user="root",
    pool_size=10,
):
    """Create or update virtualenvs on remote servers.

    Assumes that virtualenv is on the path of the remote server(s).

    :param env_name: the name of the environment in config.json.
    :param topology_name: the name of the topology (and virtualenv).
    :param virtualenv_name: the name that we should use for the virtualenv, even
                          though the topology file has a different name.
    :param requirements_paths: a list of paths to requirements files to use to
                               create virtualenv
    :param overwrite_virtualenv: Force the creation of a fresh virtualenv, even
                                 if it already exists.
    :param user: Who to delete virtualenvs as when using overwrite_virtualenv
    :param pool_size: Number of simultaneous ssh connections to use.
    """
    config = get_config()
    topology_name, topology_file = get_topology_definition(
        topology_name, config_file=config_file
    )
    topology_class = get_topology_from_file(topology_file)
    env_name, env_config = get_env_config(env_name, config_file=config_file)
    if virtualenv_name is None:
        virtualenv_name = topology_name

    config["virtualenv_specs"] = config["virtualenv_specs"].rstrip("/")

    if requirements_paths is None:
        requirements_paths = [
            os.path.join(config["virtualenv_specs"], "{}.txt".format(topology_name))
        ]

    # Check to ensure streamparse is in at least one requirements file
    found_streamparse = False
    for requirements_path in requirements_paths:
        with open(requirements_path, "r") as fp:
            for line in fp:
                if "streamparse" in line:
                    found_streamparse = True
                    break

    if not found_streamparse:
        die(
            "Could not find streamparse in one of your requirements files.  "
            "Checked {}.  streamparse is required for all topologies.".format(
                requirements_paths
            )
        )

    # Setup the fabric env dictionary
    storm_options = resolve_options(options, env_config, topology_class, topology_name)
    env_dict = get_config_dict(env_name, storm_options, config_file=config_file)

    # Actually create or update virtualenv on worker nodes
    _create_or_update_virtualenv(
        env_dict["virtualenv_root"],
        virtualenv_name,
        requirements_paths,
        virtualenv_flags=options.get("virtualenv_flags"),
        hosts=env_dict["storm_workers"],
        overwrite_virtualenv=overwrite_virtualenv,
        user=user,
        env_user=env_dict["user"],
        pool_size=pool_size,
    )


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser(
        "update_virtualenv", description=__doc__, help=main.__doc__
    )
    subparser.set_defaults(func=main)
    add_config(subparser)
    add_environment(subparser)
    add_overwrite_virtualenv(subparser)
    add_name(subparser)
    add_options(subparser)
    add_override_name(subparser)
    add_pool_size(subparser)
    add_requirements(subparser)
    add_user(subparser)


def main(args):
    """ Create or update a virtualenv on Storm workers. """
    create_or_update_virtualenvs(
        args.environment,
        args.name,
        args.options,
        virtualenv_name=args.override_name,
        requirements_paths=args.requirements,
        config_file=args.config,
        overwrite_virtualenv=args.overwrite_virtualenv,
        user=args.user,
        pool_size=args.pool_size,
    )

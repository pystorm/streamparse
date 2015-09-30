"""
Create or update a virtualenv on the Storm workers.  This will be done
automatically upon submit, but this command is provided to help with testing
and debugging.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
from io import open

from fabric.api import env, execute, parallel, prefix, put, puts, run
from fabric.contrib.files import exists

from .common import add_environment, add_name
from ..util import activate_env, die, get_config, get_topology_definition


@parallel
def _create_or_update_virtualenv(virtualenv_root,
                                 virtualenv_name,
                                 requirements_file,
                                 virtualenv_flags=None):
    virtualenv_path = os.path.join(virtualenv_root, virtualenv_name)
    if not exists(virtualenv_path):
        if virtualenv_flags is None:
            virtualenv_flags = ''
        puts("virtualenv not found in {}, creating one.".format(virtualenv_root))
        run("virtualenv {} {}".format(virtualenv_path, virtualenv_flags))

    puts("Uploading requirements.txt to temporary file.")
    tmpfile = run("mktemp /tmp/streamparse_requirements-XXXXXXXXX.txt")
    put(requirements_file, tmpfile)

    puts("Updating virtualenv: {}".format(virtualenv_name))
    cmd = "source {}".format(os.path.join(virtualenv_path, 'bin/activate'))
    with prefix(cmd):
        run("pip install -r {} --exists-action w".format(tmpfile))

    run("rm {}".format(tmpfile))


def create_or_update_virtualenvs(env_name, topology_name, requirements_file,
                                 virtualenv_flags=None):
    """Create or update virtualenvs on remote servers.

    Assumes that virtualenv is on the path of the remote server(s).

    :param env_name: the name of the environment in config.json.
    :param topology_name: the name of the topology (and virtualenv).
    :param requirements_file: path to the requirements.txt file to use
                              to update/install this virtualenv.
    """
    activate_env(env_name)
    # Check to ensure streamparse is in requirements
    with open(requirements_file, "r") as fp:
        found_streamparse = False
        for line in fp:
            if "streamparse" in line:
                found_streamparse = True
                break

        if not found_streamparse:
            die("Could not find streamparse in your requirements file ({}). "
                "streamparse is required for all topologies."
                .format(requirements_file))

    execute(_create_or_update_virtualenv, env.virtualenv_root, topology_name,
            requirements_file, virtualenv_flags=virtualenv_flags,
            hosts=env.storm_workers)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('update_virtualenv',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)
    add_name(subparser)


def main(args):
    """ Create or update a virtualenv on Storm workers. """
    name = get_topology_definition(args.name)[0]
    config = get_config()
    config["virtualenv_specs"] = config["virtualenv_specs"].rstrip("/")
    create_or_update_virtualenvs(args.environment, name,
                                 "{}/{}.txt".format(config["virtualenv_specs"],
                                                    name))

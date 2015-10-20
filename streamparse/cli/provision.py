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
def _conda_provision():
    env.use_ssh_config = True
    python_version = env.python_version
    python_bin = env.conda_root + "/bin/python"
    conda_bin = env.conda_root + "/bin/conda"
    conda_env_root = env.conda_env_root
    env_prefix = env.env_prefix
    if not exists(env_prefix):
        cmd = "{conda} create -q --yes "\
                "-p {env_prefix} "\
                "python={python_version} "\
                "pip"
        cmd = cmd.format(conda=conda_bin,
                        env_prefix=env_prefix,
                        python_version=python_version)
        run(cmd)
    pip_bin = env_prefix + "/bin/pip"
    # XXX install other requirements
    run("{pip} install streamparse".format(pip=pip_bin))


def _virtualenv_provision():
    pass


def _shell_provision():
    pass


def provision():
    provision_tasks = {
        "virtualenv": _virtualenv_provision,
        "conda": _conda_provision,
        "shell": _shell_provision
    }
    provision_task = provision_tasks.get(env.provisioner, None)
    if provision_task is None:
        raise ValueError("no provisioner found; use one of {}"
                         .format(provision_tasks.keys()))
    execute(provision_task, hosts=env.storm_workers)


@task
def provision_topology(name=None, env_name="prod"):
    prepare_topology()

    env = activate_env(env_name)

    if env.provisioner == "virtualenv":
        # XXX: no need for this step here anymore?
        create_or_update_virtualenvs(
            name, "{}/{}.txt".format(env.virtualenv_specs, name)
        )
        prefix = "{virtualenv_root}/{topology_name}".format(
                    virtualenv_root=env.virtualenv_root,
                    topology_name=name)
        env.env_prefix = prefix
    elif env.provisioner == "conda":
        prefix = "{conda_env_root}/{topology_name}".format(
                    conda_env_root=env.conda_env_root,
                    topology_name=name)
        env.env_prefix = prefix
    elif env.provisioner == "shell":
        env.env_prefix = "/usr"
    else:
        raise ValueError("Invalid provisioner specified: {!r}".format(env_config["provisioner"]))
    provision()


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

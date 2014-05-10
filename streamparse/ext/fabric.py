"""streamparse.ext.fabric

fabric tasks that are imported into a project's fabfile.py.

Should be used like this::

    from fabric.api import *
    from streamparse.ext.fabric import *

    # your other tasks
"""
from __future__ import absolute_import, print_function

from fabric.api import *
from fabric.contrib.files import exists

from .util import get_env_config


__all__ = ["activate_env", "create_or_update_virtualenvs"]


@task
def activate_env(env_name=None):
    """Activate a particular environment from a streamparse project's
    config.json file and populatefabric's env dictionary with appropriate
    values.

    :param env_name: a `str` corresponding to the key within the config file's
    "envs" dictionary.
    """
    env_name, env_config = get_env_config(env_name)

    # get the host only (not port) for Nimbus since we'll be using SSH anyway
    # env.storm_nimbus = [env_config["nimbus"].split(":")[0]]
    env.storm_workers = env_config["workers"]
    env.user = env_config["user"]
    env.log_path = env_config["log_path"]
    env.virtualenv_path = env_config["virtualenv_path"]


@parallel
def _create_or_update_virtualenv(virtualenvs_path, virtualenv_name,
                                requirements_file):
    """Create or update a virtualenv on a remote server.  Assumes that
    virtualenv is on the path of the server.

    :param virtualenvs_path: a `str` denoting where virtualenvs should be
    stored on the server.
    :param virtualenv_name: a `str` indicating the name of the virtualenv to
    create or update.
    :param requirements_file: a `str` which is the path to a local requirements
    file to use for "pip install -r ..." on the server.
    """
    if not exists("{}/{}".format(virtualenvs_path, virtualenv_name)):
        puts("virtualenv not found for {}, creating one.".format(virtualenvs_path))
        run("virtualenv {}/{}".format(virtualenvs_path, virtualenv_name))

    puts("Uploading requirements.txt to temporary file.")
    tmpfile = run("mktemp /tmp/streamparse_requirements-XXXXXXXXX.txt")
    put(requirements_file, tmpfile)

    puts("Updating virtualenv: {}".format(virtualenv_name))
    cmd = "source {}/{}/bin/activate".format(virtualenvs_path, virtualenv_name)
    with prefix(cmd):
        run("pip install streamparse")
        run("pip install -r {}".format(tmpfile))

    run("rm {}".format(tmpfile))


@task
def create_or_update_virtualenvs(virtualenv_name, requirements_file):
    """Create or update virtualenvs on remote servers.  Assumes that virtualenv
    is on the path of the remote server(s).

    :param virtualenv_name: a `str`, the name of the virtualenv.
    :param requirements_file: a `str` path to the requirements.txt file to use
    to update/install this virtualenv.
    """
    execute(_create_or_update_virtualenv, env.virtualenv_path, virtualenv_name,
            requirements_file, hosts=env.storm_workers)

"""streamparse.ext.fabric

fabric tasks that are imported into a project's fabfile.py.

Should be used like this::

    from fabric.api import *
    from streamparse.ext.fabric import *

    # your other tasks
"""
from __future__ import absolute_import, print_function, unicode_literals

import os
from io import open

from fabric.api import env, execute, parallel, prefix, put, puts, run, task
from fabric.contrib.files import exists

from .util import get_env_config, die


__all__ = ["activate_env", "create_or_update_virtualenvs", "tail_logs",
           "remove_logs"]


@parallel
def _remove_logs(topology_name):
    print("Removing all \"{}\" topology Python logs on {!r}"
          .format(topology_name, env.storm_workers))
    log_path = "{}/".format(env.log_path) if not env.log_path.endswith("/") \
               else env.log_path
    find_cmd = ("find {log_path}/ -name \"streamparse_{topo_name}*\""
                .format(log_path=log_path, topo_name=topology_name))
    rm_cmd = "{} | xargs rm".format(find_cmd)
    run(rm_cmd, warn_only=True)


@task
def remove_logs(topology_name):
    """Remove all Python logs on Storm workers in the log.path directory."""
    execute(_remove_logs, topology_name, hosts=env.storm_workers)


@task
def _tail_logs(topology_name=None, pattern=None):
    # list log files found
    ls_cmd = ("cd {log_path} && ls worker* supervisor* access* metrics* "
              "streamparse_{topo_name}_*"
              .format(log_path=env.log_path, topo_name=topology_name))
    if pattern is not None:
        ls_cmd += " | egrep '{pattern}'".format(pattern=pattern)
    run(ls_cmd)
    tail_pipe = " | xargs tail -f"
    run(ls_cmd + tail_pipe)


@task
def tail_logs(topology_name=None, pattern=None):
    """Follow (tail -f) the log files on remote Storm workers.

    Will use the `log_path` and `workers` properties from config.json.
    """
    execute(_tail_logs, topology_name, pattern, hosts=env.storm_workers)


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
    env.log_path = env_config.get("log_path") or \
                   env_config.get("log", {}).get("path")
    env.provisioner = env_config.get("provisioner", "virtualenv")
    if env.provisioner == "virtualenv":
        env.virtualenv_root = env_config.get("virtualenv_root") or \
                              env_config.get("virtualenv_path")
        env.virtualenv_specs = env_config.get("virtualenv_specs")
    elif env.provisioner == "conda":
        conda_config = env_config.get("conda")
        env.conda_root = conda_config.get("conda_root")
        env.conda_env_root = conda_config.get("conda_env_root")
        env.python_version = conda_config.get("python_version")
    elif env.provisioner == "shell":
        env.shell_cmd = "foo"
    env.disable_known_hosts = True
    env.forward_agent = True
    return env


@parallel
def _create_or_update_virtualenv(virtualenv_root,
                                 virtualenv_name,
                                 requirements_file):
    virtualenv_path = os.path.join(virtualenv_root, virtualenv_name)
    if not exists(virtualenv_path):
        puts("virtualenv not found in {}, creating one.".format(virtualenv_root))
        run("virtualenv {}".format(virtualenv_path))

    puts("Uploading requirements.txt to temporary file.")
    tmpfile = run("mktemp /tmp/streamparse_requirements-XXXXXXXXX.txt")
    put(requirements_file, tmpfile)

    puts("Updating virtualenv: {}".format(virtualenv_name))
    cmd = "source {}".format(os.path.join(virtualenv_path, 'bin/activate'))
    with prefix(cmd):
        run("pip install -r {}".format(tmpfile))

    run("rm {}".format(tmpfile))

@parallel
def _conda_provision():
    env.use_ssh_config = True
    python_version = env.python_version
    python_bin = env.conda_root + "/bin/python"
    conda_bin = env.conda_root + "/bin/conda"
    conda_env_root = env.conda_env_root
    env_prefix = "{conda_env_root}/{topology_name}".format(
                conda_env_root=conda_env_root,
                topology_name="wordcount-mem")
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


@task
def provision():
    if env.provisioner == "conda":
        execute(_conda_provision, hosts=env.storm_workers)
    else:
        raise ValueError("no provisioner found")

@task
def create_or_update_virtualenvs(virtualenv_name, requirements_file):
    """Create or update virtualenvs on remote servers.

    Assumes that virtualenv is on the path of the remote server(s).

    :param virtualenv_name: the name of the virtualenv.
    :param requirements_file: path to the requirements.txt file to use
    to update/install this virtualenv.
    """
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

    execute(_create_or_update_virtualenv,
            env.virtualenv_root,
            virtualenv_name,
            requirements_file,
            hosts=env.storm_workers)

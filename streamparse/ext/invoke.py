"""streamparse.ext.invoke

invoke tasks that are imported into a project's task.py.

Should be used like this::

    from invoke import task, run
    from streamparse.ext.invoke import *

    # your other tasks
"""
from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import shutil
import time
from io import open
from tempfile import NamedTemporaryFile

from invoke import run, task

from ..contextmanagers import ssh_tunnel
from .util import (get_env_config, get_topology_definition,
                   get_nimbus_for_env_config, get_config)
from .fabric import activate_env, create_or_update_virtualenvs, tail_logs



__all__ = ["list_topologies", "kill_topology", "run_local_topology",
           "submit_topology", "tail_topology"]

# TODO: remove boilerplate get_env_config, get_nimbus_for_env_config...
# from all these with something like
# @task("setup")

def is_safe_to_submit(topology_name):
    """Check to see if a topology is currently running or is in the process of
    being killed. Assumes tunnel is already connected to Nimbus."""
    result = _list_topologies(run_kwargs={"hide": "both"})

    if result.failed:
        raise Exception("Error running streamparse.commands.list/-main")

    pattern = re.compile(r"{}\s+\|\s+(ACTIVE|KILLED)\s+\|"
                         .format(topology_name))
    if re.search(pattern, result.stdout):
        return False
    else:
        return True


@task
def prepare_topology():
    """Prepare a topology for running locally or deployment to a remote
    cluster.
    """
    if os.path.isdir("_resources/resources"):
        shutil.rmtree("_resources/resources")
    shutil.copytree("src", "_resources/resources")


def _list_topologies(run_args=None, run_kwargs=None):
    if run_args is None:
        run_args = []
    if run_kwargs is None:
        run_kwargs = {}
    cmd = ["lein",
           "run -m streamparse.commands.list/-main"]
    return run(" ".join(cmd), *run_args, **run_kwargs)


@task
def list_topologies(env_name="prod"):
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    with ssh_tunnel(env_config["user"], host, 6627, port):
        return _list_topologies()


def _kill_topology(topology_name, run_args=None, run_kwargs=None):
    if run_args is None:
        run_args = []
    if run_kwargs is None:
        run_kwargs = {}
    cmd = ["lein",
           "run -m streamparse.commands.kill_topology/-main",
           topology_name]
    return run(" ".join(cmd), *run_args, **run_kwargs)


@task
def kill_topology(topology_name=None, env_name="prod"):
    topology_name, topology_file = get_topology_definition(topology_name)
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    with ssh_tunnel(env_config["user"], host, 6627, port):
        return _kill_topology(topology_name)


@task
def jar_for_deploy():
    print("Cleaning from prior builds...")
    res = run("lein clean", hide="stdout")
    if not res.ok:
        raise Exception("Unable to run 'lein clean'!\nSTDOUT:\n{}"
                        "\nSTDERR:\n{}".format(res.stdout, res.stderr))
    print("Creating topology JAR...")
    res = run("lein jar", hide="stdout")
    if not res.ok:
        raise Exception("Unable to run 'lein jar'!\nSTDOUT:\n{}"
                        "\nSTDERR:\n{}".format(res.stdout, res.stderr))
    # XXX: This will fail if more than one JAR is built
    lines = [l.strip().lstrip("Created ") for l in res.stdout.split()
             if l.endswith(".jar")]
    return lines[0]


@task(pre=["prepare_topology"])
def run_local_topology(name=None, time=5, par=2, options=None, debug=False):
    """Run a topology locally using Storm's LocalCluster class."""
    prepare_topology()

    name, topology_file = get_topology_definition(name)
    print("Running {} topology...".format(name))
    cmd = ["lein",
           "run -m streamparse.commands.run/-main",
           topology_file]
    cmd.append("-t {}".format(time))
    if debug:
        cmd.append("--debug")
    cmd.append('--option "topology.workers={}"'.format(par))
    cmd.append('--option "topology.acker.executors={}"'.format(par))
    if options is None:
        options = []
    for option in options:
        cmd.append('--option {}'.format(option))
    full_cmd = " ".join(cmd)
    print("Running lein command to run local cluster:")
    print(full_cmd)
    run(full_cmd)


@task(pre=["prepare_topology"])
def submit_topology(name=None, env_name="prod", par=2, options=None,
                    force=False, debug=False):
    """Submit a topology to a remote Storm cluster."""
    prepare_topology()

    config = get_config()
    name, topology_file = get_topology_definition(name)
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    config["virtualenv_specs"] = config["virtualenv_specs"].rstrip("/")
    activate_env(env_name)
    create_or_update_virtualenvs(name,
                                 "{}/{}.txt".format(config["virtualenv_specs"],
                                                    name))

    # TODO: Super hacky way to replace "python" with our venv executable, need
    # to fix this
    with open(topology_file, "r") as fp:
        contents = fp.read()
    contents = re.sub(r'"python"',
                     '"{}/{}/bin/python"'
                      .format(env_config["virtualenv_root"], name),
                      contents)
    tmpfile = NamedTemporaryFile(dir=config["topology_specs"])
    tmpfile.write(contents)
    tmpfile.flush()
    print("Created modified topology definition file {}.".format(tmpfile.name))

    # replaced with /path/to/venv/bin/python instead

    # Prepare a JAR that doesn't have Storm dependencies packaged
    topology_jar = jar_for_deploy()

    print('Deploying "{}" topology...'.format(name))
    with ssh_tunnel(env_config["user"], host, 6627, port):
        print("ssh tunnel to Nimbus {}:{} established."
              .format(host, port))

        if force and not is_safe_to_submit(name):
            print("Killing current \"{}\" topology.".format(name))
            _kill_topology(name, run_kwargs={"hide": "both"})
            while not is_safe_to_submit(name):
                print("Waiting for topology {} to quit...".format(name))
                time.sleep(0.5)

            print("Killed.")

        jvm_opts = [
            "-Dstorm.jar={}".format(topology_jar),
            "-Dstorm.options=",
            "-Dstorm.conf.file=",
        ]
        os.environ["JVM_OPTS"] = " ".join(jvm_opts)
        cmd = ["lein",
               "run -m streamparse.commands.submit_topology/-main",
               tmpfile.name]
        if debug:
            cmd.append("--debug")
        cmd.append('--option "topology.workers={}"'.format(par))
        cmd.append('--option "topology.acker.executors={}"'.format(par))
        if options is None:
            options = []
        for option in options:
            cmd.append('--option {}'.format(option))
        full_cmd = " ".join(cmd)
        print("Running lein command to submit topology to nimbus:")
        print(full_cmd)
        run(full_cmd)

    tmpfile.close()

@task
def tail_topology(env_name="prod", pattern=None):
    activate_env(env_name)
    tail_logs(pattern)

@task
def visualize_topology(name=None, flip=False):
    name, topology_file = get_topology_definition(name)
    print("Visualizing {} topology...".format(name))
    cmd = ["lein",
           "run -m streamparse.commands.visualize/-main",
           topology_file]
    if flip:
        cmd.append("-f")
    full_cmd = " ".join(cmd)
    print("Running lein command to visualize topology:")
    print(full_cmd)
    run(full_cmd)


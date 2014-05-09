"""streamparse.ext.invoke

invoke tasks that are imported into a project's task.py.

Should be used like this::

    from invoke import task, run
    from streamparse.ext.invoke import *

    # your other tasks
"""
from __future__ import absolute_import, print_function
import os
import shutil
import sys
import json
from glob import glob
import subprocess

from invoke import run, task

from .util import get_config, die
from ..contextmanagers import ssh_tunnel


__all__ = ["run_local_topology", "deploy_topology"]


def stormdeps(topology=None):
    print("Storm dependencies (via lein):")
    run("lein deps :tree")
    print("Python dependencies (via pip):")
    run("cat virtualenvs/{}".format(topology))


def _get_topology(name=None):
    """Fetch a topology name and definition file.  If the name is None, we'll
    select the first .clj file in the topologies/ directory.

    :returns: a `tuple` containing (topology_name, topology_file)
    """
    config = get_config()
    topology_path = config["topology_specs"]
    if name is None:
        topology_files = glob("{}/*.clj".format(topology_path))
        if not topology_files:
            die("No topology definitions are defined in {}."
                .format(topology_path))
        topology_file = topology_files[0]
        name = topology_file.rstrip(".clj").lstrip(topology_path)
    else:
        topology_file = "{}.clj".format(os.path.join(topology_path, name))
        if not os.path.exists(topology_file):
            die("Topology definition file not found {}. You need to "
                "create a topology definition file first."
                .format(topology_file))

    return (name, topology_file)


@task
def uberjar_for_deploy():
    print("Creating jar for topology...")
    res = run("lein with-profile deploy uberjar", hide="stdout")
    if not res.ok:
        raise Exception("Unable to uberjar!\nSTDOUT:\n{}"
                        "\nSTDERR:\n{}".format(res.stdout, res.stderr))

    return res.stdout.split("\n")[0]


@task
def run_local_topology(name=None, time=5, debug=False):
    name, topology_file = _get_topology(name)
    print("Running {} topology...".format(name))
    if os.path.isdir("_resources/resources"):
        shutil.rmtree("_resources/resources")
    shutil.copytree("src", "_resources/resources")
    cmd = ["lein run -m streamparse.commands.run/-main", topology_file,
           "-t", str(time)]
    if debug:
        cmd.append("--debug")
    print(" ".join(cmd))
    run(" ".join(cmd))


@task
def deploy_topology(name=None, env="prod", debug=False):
    config = get_config()
    env = config["envs"][env]
    name, topology_file = _get_topology(name)
    if ":" in env["nimbus"]:
        host, port = env["nimbus"].split(":", 1)
        port = int(port)
    else:
        host = env["nimbus"]
        port = 6627

    # Prepare a JAR that doesn't have Storm dependencies packaged
    topology_jar = uberjar_for_deploy()

    print("Deploying {} topology...".format(name))
    with ssh_tunnel(env["user"], host, 6627, port):
        print("ssh tunnel to Nimbus established.")
        os.environ["JVM_OPTS"] = "-Dstorm.jar={}".format(topology_jar)
        cmd = ["lein",
               "with-profile deploy",
               "run -m streamparse.commands.submit_topology/-main",
               topology_file]
        print(" ".join(cmd))
        run(" ".join(cmd))


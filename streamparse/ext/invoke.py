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
from tempfile import NamedTemporaryFile
import re

from invoke import run, task

from ..contextmanagers import ssh_tunnel
from .util import (get_env_config, get_topology_definition,
                   get_nimbus_for_env_config, get_config)
from .fabric import activate_env, create_or_update_virtualenvs, tail_logs



__all__ = ["list_topologies",  "kill_topology", "run_local_topology",
           "submit_topology", "tail_topology"]

# TODO: remove boilerplate get_env_config, get_nimbus_for_env_config...
# from all these with something like
# @task("setup")

@task
def prepare_topology():
    """Prepare a topology for running locally or deployment to a remote
    cluster.
    """
    if os.path.isdir("_resources/resources"):
        shutil.rmtree("_resources/resources")
    shutil.copytree("src", "_resources/resources")


@task
def list_topologies(env_name="prod"):
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    with ssh_tunnel(env_config["user"], host, 6627, port):
        cmd = ["lein",
               "run -m streamparse.commands.list/-main"]
        run(" ".join(cmd))


@task
def kill_topology(topology_name=None, env_name="prod"):
    topology_name, topology_file = get_topology_definition(topology_name)
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    with ssh_tunnel(env_config["user"], host, 6627, port):
        cmd = ["lein",
               "run -m streamparse.commands.kill_topology/-main",
               topology_name]
        run(" ".join(cmd))


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
def run_local_topology(name=None, time=5, debug=False):
    """Run a topology locally using Storm's LocalCluster class."""
    prepare_topology()

    name, topology_file = get_topology_definition(name)
    print("Running {} topology...".format(name))
    cmd = ["lein run -m streamparse.commands.run/-main", topology_file,
           "-t", str(time)]
    if debug:
        cmd.append("--debug")
    run(" ".join(cmd))


@task(pre=["prepare_topology"])
def submit_topology(name=None, env_name="prod", debug=False):
    """Submit a topology to a remote Storm cluster."""
    prepare_topology()

    config = get_config()
    name, topology_file = get_topology_definition(name)
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

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
                      .format(env_config["virtualenv_path"], name),
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
        run(" ".join(cmd))

    tmpfile.close()

@task
def tail_topology(env_name="prod"):
    activate_env(env_name)
    tail_logs()

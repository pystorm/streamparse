"""streamparse.ext.invoke

invoke tasks that are imported into a project's task.py.

Should be used like this::

    from invoke import task, run
    from streamparse.ext.invoke import *

    # your other tasks
"""
from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import json
from glob import glob

from invoke import run, task
from fabric.colors import red


__all__ = ["stormlocal", "run_local_topology"]

def print_error(msg, error_code=1):
    print("{}: {}".format(red("error"), msg))
    sys.exit(error_code)


def stormdeps(topology=None):
    print("Storm dependencies (via lein):")
    run("lein deps :tree")
    print("Python dependencies (via pip):")
    run("cat virtualenvs/{}".format(topology))


@task
def stormlocal(topology_file, time="5000", debug=False):
    time = time or "5000"
    run("mkdir -p _resources/resources")
    run("cp src/*.py _resources/resources/")
    cmd = ["lein run -s", topology_file, "-t", time]
    if debug:
        cmd.append("-d")
    run(' '.join(cmd))


@task
def run_local_topology(name=None, time="5000", debug=False):
    if not os.path.exists("config.json"):
        print_error("No config.json found. You must run this command inside a"
                    "streamparse project directory.")

    with open("config.json") as fp:
        config = json.load(fp)

    topology_path = config["topology_specs"]
    # Select the first topology definition file that we find in
    # alphabetical order
    if name is None:
        topology_files = glob("{}/*.clj".format(topology_path))
        if not topology_files:
            print_error("No topology definitions are defined in {}."
                        .format(topology_path))
        topology_file = topology_files[0]
        name = topology_file.rstrip(".clj").lstrip(topology_path)
    else:
        topology_file = "{}.clj".format(os.path.join(topology_path, name))
        if not os.path.exists(topology_file):
            print_error("Topology definition file not found {}. You need to "
                        "create a topology definition file first."
                        .format(topology_file))

    print("Running {} topology...".format(name))
    stormlocal(topology_file, time, debug)

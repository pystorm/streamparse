"""streamparse.ext.invoke

invoke tasks that are imported into a project's task.py.

Should be used like this::

    from invoke import task, run
    from streamparse.ext.invoke import *

    # your other tasks
"""
from __future__ import absolute_import
from __future__ import print_function

from invoke import run, task

__all__ = ["stormlocal"]

def stormdeps(topology=None):
    print("Storm dependencies (via lein):")
    run("lein deps :tree")
    print("Python dependencies (via pip):")
    run("cat virtualenvs/{}".format(topology))

@task
def stormlocal(topology=None, time="5000", debug=False):
    if topology is None:
        print("Must specify topology for stormlocal")
        return
    run("mkdir -p _resources/resources")
    run("cp src/*.py _resources/resources/")
    cmd = "lein run -s {} -t {}".format(topology, time)
    if debug:
        cmd += " -d"
    run(cmd)

"""streamparse.ext.invoke

invoke tasks that are imported into a project's task.py.

Should be used like this::

    from invoke import task, run
    from streamparse.ext.invoke import *

    # your other tasks
"""
from __future__ import absolute_import

from invoke import run, task

__all__ = ["stormlocal"]

@task
def stormlocal(topology=None):
    run("lein run -s {}".format(topology))

"""streamparse.ext.fabric

fabric tasks that are imported into a project's fabfile.py.

Should be used like this::

    from fabric.api import *
    from streamparse.ext.fabric import *

    # your other tasks
"""
from __future__ import absolute_import
import json
import os

from fabric.api import *
from .util import get_config

# __all__ = ["setup_virtualenv", "workers"]
__all__ = ['env', 'deploy_topology', 'uberjar', 'deploy_virtualenv',
           'submit_topology']


@task
def env(env_=None):
    """Activate a particular environment from the config.json file."""
    with open('config.json', 'r') as fp:
        config = json.load(fp)
    _env.nimbus = config['envs'][env_]['hosts']['nimbus']
    _env.workers = config['envs'][env_]['hosts']['workers']


@task
def deploy_topology(topology=None):
    """Deploy a topology to a remote host.  Deploying a streamparse topology
    accomplishes two things:
    1. Create an uberjar which contains all code.
    2. Push the topology virtualenv requirements to remote.
    3. Update virtualenv on host server.
    4. Submit topology (in uberjar) to remote Storm cluster."""
    pass


@task
def uberjar():
    """Create a JAR which contains all required dependencies for execution on a
    Storm cluster."""
    pass


@task
def deploy_virtualenv():
    """Deploy and update the virtualenv on all Storm worker nodes."""
    pass

@task
def submit_topology(topology_name, timeout=None):
    """Submit a Storm topology to the Nimbus machine in a Storm cluster."""
    pass

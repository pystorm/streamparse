"""fab env:prod deploy:wordcount"""
import json

from fabric.api import run, put, env as _env
from fabric.decorators import task


@task
def env(e=None):
    """Activate a particular environment from the config.json file."""
    with open('config.json', 'r') as fp:
        config = json.load(fp)
    _env.hosts = config['envs'][e]['hosts']


@task
def deploy(topology=None):
    """Deploy a topology to a remote host.  Deploying a streamparse topology
    accomplishes two things:
    1. Create an uberjar which contains all code.
    2. Push the topology virtualenv requirements to remote.
    3. Update virtualenv on host server.
    4. Submit topology (in uberjar) to remote Storm cluster."""
    pass

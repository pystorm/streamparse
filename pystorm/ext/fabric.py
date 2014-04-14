"""pystorm.fabric

fabric tasks that are imported into a project's fabfile.py.

Should be used like this::

    from fabric.api import *
    from pystorm.ext.fabric import *

    # your other tasks
"""
from __future__ import absolute_import

from fabric.api import *
from .util import get_config

__all__ = ["setup_virtualenv", "workers"]

# XXX really hacky, will clean this up -- just playing

prod_config = get_config()["envs"]["prod"]
prod_nimbus = [prod_config["nimbus"]]
prod_workers = prod_config["workers"]
prod_user = prod_config["user"]

beta_config = get_config()["envs"]["beta"]
beta_nimbus = [beta_config["nimbus"]]
beta_workers = beta_config["workers"]
beta_user = beta_config["user"]


@task
def workers(deploy_env="beta"):
    user = prod_user if deploy_env == "prod" else beta_user
    env.user = user
    workers = prod_workers if deploy_env == "prod" else beta_workers
    env.hosts = workers


@task
def setup_virtualenv(topology=None):
    run("ls")

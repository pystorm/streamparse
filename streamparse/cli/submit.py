"""
Submit a Storm topology to Nimbus.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import sys
import time

from invoke import run
from six import string_types

from ..contextmanagers import ssh_tunnel
from ..thrift import storm_thrift
from ..util import (activate_env, get_config, get_env_config,
                    get_nimbus_client, get_topology_definition,
                    is_ssh_for_nimbus)
from .common import (add_ackers, add_debug, add_environment, add_name,
                     add_options, add_par, add_simple_jar, add_wait,
                     add_workers, resolve_ackers_workers)
from .jar import jar_for_deploy
from .kill import _kill_topology
from .list import _list_topologies
from .update_virtualenv import create_or_update_virtualenvs


def get_user_tasks():
    """Get tasks defined in a user's tasks.py and fabric.py file which is
    assumed to be in the current working directory.

    :returns: a `tuple` (invoke_tasks, fabric_tasks)
    """
    sys.path.insert(0, os.getcwd())
    try:
        import tasks as user_invoke
    except ImportError:
        user_invoke = None
    try:
        import fabfile as user_fabric
    except ImportError:
        user_fabric = None
    return user_invoke, user_fabric


def is_safe_to_submit(topology_name, nimbus_client):
    """Is topology not running or deactivated?"""
    topologies = _list_topologies(nimbus_client)
    safe = True
    for topology in topologies:
        if topology.name == topology_name:
            # Only safe if topology isn't running or is deactivated
            safe = topology.status.upper() not in ('ACTIVE', 'KILLED')
            break
    return safe


def _kill_existing_topology(topology_name, force, wait, nimbus_client):
    if force and not is_safe_to_submit(topology_name, nimbus_client):
        print("Killing current \"{}\" topology.".format(topology_name))
        sys.stdout.flush()
        _kill_topology(topology_name, nimbus_client, wait=wait)
        while not is_safe_to_submit(topology_name, nimbus_client):
            print("Waiting for topology {} to quit...".format(topology_name))
            sys.stdout.flush()
            time.sleep(0.5)
        print("Killed.")
        sys.stdout.flush()


def _submit_topology(topology_name, topology_file, topology_jar, env_config,
                     workers, ackers, nimbus_client, options=None, debug=False):
    jvm_opts = [
        "-Dstorm.jar={}".format(topology_jar),
        "-Dstorm.options=",
        "-Dstorm.conf.file=",
    ]
    os.environ["JVM_OPTS"] = " ".join(jvm_opts)
    storm_options = {'topology.workers': workers,
                     'topology.acker.executors': ackers,
                     'topology.debug': debug}

    if env_config.get('use_virtualenv', True):
        python_path = '/'.join([env_config["virtualenv_root"],
                                topology_name, "bin", "python"])
        storm_options['topology.python.path'] = python_path

    # Python logging settings
    log_config = env_config.get("log", {})
    log_path = log_config.get("path") or env_config.get("log_path")
    print("Routing Python logging to {}.".format(log_path))
    sys.stdout.flush()
    if log_path:
        storm_options['streamparse.log.path'] = log_path
    if isinstance(log_config.get("max_bytes"), int):
        storm_options['streamparse.log.max_bytes'] = log_config["max_bytes"]
    if isinstance(log_config.get("backup_count"), int):
        storm_options['streamparse.log.backup_count'] = log_config["backup_count"]
    if isinstance(log_config.get("level"), string_types):
        storm_options['streamparse.log.level'] = log_config["level"].lower()

    if options is None:
        options = []
    for option in options:
        key, val = option.split("=", 1)
        option[key] = val
    print("Submitting topology to nimbus:")
    sys.stdout.flush()
    run()
    nimbus_client.beginFileUpload()
    nimbus_client.beginFileUpload()
    nimbus_client.submit_topology(topology_name, )

def _pre_submit_hooks(topology_name, env_name, env_config):
    """Pre-submit hooks for invoke and fabric."""
    user_invoke, user_fabric = get_user_tasks()
    pre_submit_invoke = getattr(user_invoke, "pre_submit", None)
    if callable(pre_submit_invoke):
        pre_submit_invoke(topology_name, env_name, env_config)
    pre_submit_fabric = getattr(user_fabric, "pre_submit", None)
    if callable(pre_submit_fabric):
        pre_submit_fabric(topology_name, env_name, env_config)


def _post_submit_hooks(topology_name, env_name, env_config):
    """Post-submit hooks for invoke and fabric."""
    user_invoke, user_fabric = get_user_tasks()
    post_submit_invoke = getattr(user_invoke, "post_submit", None)
    if callable(post_submit_invoke):
        post_submit_invoke(topology_name, env_name, env_config)
    post_submit_fabric = getattr(user_fabric, "post_submit", None)
    if callable(post_submit_fabric):
        post_submit_fabric(topology_name, env_name, env_config)


def submit_topology(name=None, env_name="prod", workers=2, ackers=2,
                    options=None, force=False, debug=False, wait=None,
                    simple_jar=False):
    """Submit a topology to a remote Storm cluster."""
    config = get_config()
    name, topology_file = get_topology_definition(name)
    env_name, env_config = get_env_config(env_name)
    nimbus_client = get_nimbus_client(env_config)

    # Check if we need to maintain virtualenv during the process
    use_venv = env_config.get('use_virtualenv', True)
    # Setup the fabric env dictionary
    activate_env(env_name)
    # Run pre_submit actions provided by project
    _pre_submit_hooks(name, env_name, env_config)

    if use_venv:
        config["virtualenv_specs"] = config["virtualenv_specs"].rstrip("/")
        create_or_update_virtualenvs(
            env_name,
            name,
            "{}/{}.txt".format(config["virtualenv_specs"], name),
            virtualenv_flags=env_config.get('virtualenv_flags'))

    # Prepare a JAR that doesn't have Storm dependencies packaged
    topology_jar = jar_for_deploy(simple_jar=simple_jar)

    print('Deploying "{}" topology...'.format(name))
    sys.stdout.flush()
    _kill_existing_topology(name, force, wait, nimbus_client)
    _submit_topology(name, topology_file, topology_jar, env_config, workers,
                     ackers, nimbus_client, options=options, debug=debug)
    _post_submit_hooks(name, env_name, env_config)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('submit',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_ackers(subparser)
    add_debug(subparser)
    add_environment(subparser)
    subparser.add_argument('-f', '--force',
                           action='store_true',
                           help='Force a topology to submit by killing any '
                                'currently running topologies with the same '
                                'name.')
    add_name(subparser)
    add_options(subparser)
    add_par(subparser)
    add_simple_jar(subparser)
    add_wait(subparser)
    add_workers(subparser)


def main(args):
    """ Submit a Storm topology to Nimbus. """
    resolve_ackers_workers(args)
    submit_topology(name=args.name, env_name=args.environment,
                    workers=args.workers, ackers=args.ackers,
                    options=args.options, force=args.force, debug=args.debug,
                    wait=args.wait, simple_jar=args.simple_jar)

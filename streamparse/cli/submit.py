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

from .common import (add_ackers, add_debug, add_environment, add_name,
                     add_options, add_par, add_simple_jar, add_wait,
                     add_workers, resolve_ackers_workers)
from .jar import jar_for_deploy
from .kill import _kill_topology
from .list import _list_topologies
from .update_virtualenv import create_or_update_virtualenvs
from ..contextmanagers import ssh_tunnel
from ..util import (activate_env, get_config, get_env_config,
                    get_nimbus_for_env_config, get_topology_definition,
                    is_ssh_for_nimbus)


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


def is_safe_to_submit(topology_name, host=None, port=None):
    """Check to see if a topology is currently running or is in the process of
    being killed. Assumes tunnel is already connected to Nimbus."""
    result = _list_topologies(run_kwargs={"hide": "both"},
                              host=host, port=port)

    if result.failed:
        raise RuntimeError("Error running streamparse.commands.list/-main")

    pattern = re.compile(r"{}\s+\|\s+(ACTIVE|KILLED)\s+\|"
                         .format(topology_name))
    if re.search(pattern, result.stdout):
        return False
    else:
        return True


def _kill_existing_topology(topology_name, force, wait, host=None, port=None):
    if force and not is_safe_to_submit(topology_name, host=host, port=port):
        print("Killing current \"{}\" topology.".format(topology_name))
        sys.stdout.flush()
        _kill_topology(topology_name, run_kwargs={"hide": "both"},
                       wait=wait, host=host, port=port)
        while not is_safe_to_submit(topology_name, host=host, port=port):
            print("Waiting for topology {} to quit...".format(topology_name))
            sys.stdout.flush()
            time.sleep(0.5)
        print("Killed.")
        sys.stdout.flush()


def _submit_topology(topology_name, topology_file, topology_jar,
                     env_config, workers, ackers, options=None, debug=False,
                     host=None, port=None):
    jvm_opts = [
        "-Dstorm.jar={}".format(topology_jar),
        "-Dstorm.options=",
        "-Dstorm.conf.file=",
    ]
    os.environ["JVM_OPTS"] = " ".join(jvm_opts)
    cmd = [
        "lein",
        "run -m streamparse.commands.submit_topology/-main",
        topology_file]

    if host:
        cmd.append("--host {}".format(host))
    if port:
        cmd.append("--port {}".format(port))
    if debug:
        cmd.append("--debug")

    cmd.append("--option 'topology.workers={}'".format(workers))
    cmd.append("--option 'topology.acker.executors={}'".format(ackers))

    if env_config.get('use_virtualenv', True):
        python_path = '/'.join([env_config["virtualenv_root"],
                                topology_name, "bin", "python"])

        cmd.append("--option 'topology.python.path=\"{}\"'".format(python_path))

    # Python logging settings
    log_config = env_config.get("log", {})
    log_path = log_config.get("path") or env_config.get("log_path")
    print("Routing Python logging to {}.".format(log_path))
    sys.stdout.flush()
    if log_path:
        cmd.append("--option 'streamparse.log.path=\"{}\"'"
                   .format(log_path))
    if isinstance(log_config.get("max_bytes"), int):
        cmd.append("--option 'streamparse.log.max_bytes={}'"
                   .format(log_config["max_bytes"]))
    if isinstance(log_config.get("backup_count"), int):
        cmd.append("--option 'streamparse.log.backup_count={}'"
                   .format(log_config["backup_count"]))
    if isinstance(log_config.get("level"), string_types):
        cmd.append("--option 'streamparse.log.level=\"{}\"'"
                   .format(log_config["level"].lower()))

    if options is None:
        options = []
    for option in options:
        # XXX: hacky Parse.ly-related workaround; must fix root
        # issue with -o options and string values
        if "deployment_stage" in option:
            key, val = option.split("=")
            cmd.append("--option '{}=\"{}\"'".format(key, val))
        else:
            cmd.append("--option {}".format(option))
    full_cmd = " ".join(cmd)
    print("Running lein command to submit topology to nimbus:")
    print(full_cmd)
    sys.stdout.flush()
    run(full_cmd)


def _pre_submit_hooks(topology_name, env_name, env_config):
    """Pre-submit hooks for invoke and fabric.
    """
    user_invoke, user_fabric = get_user_tasks()
    pre_submit_invoke = getattr(user_invoke, "pre_submit", None)
    if callable(pre_submit_invoke):
        pre_submit_invoke(topology_name, env_name, env_config)
    pre_submit_fabric = getattr(user_fabric, "pre_submit", None)
    if callable(pre_submit_fabric):
        pre_submit_fabric(topology_name, env_name, env_config)


def _post_submit_hooks(topology_name, env_name, env_config):
    """Post-submit hooks for invoke and fabric.
    """
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
    host, port = get_nimbus_for_env_config(env_config)

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
    # Use ssh tunnel with Nimbus or use host/port for Thrift connection
    if is_ssh_for_nimbus(env_config):
        with ssh_tunnel(env_config.get("user"), host, 6627, port):
            print("ssh tunnel to Nimbus {}:{} established.".format(host, port))
            sys.stdout.flush()
            _kill_existing_topology(name, force, wait)
            _submit_topology(name, topology_file, topology_jar,
                             env_config, workers, ackers, options, debug)
            _post_submit_hooks(name, env_name, env_config)
    else:
        # This part doesn't use SSH tunnel at all
        _kill_existing_topology(name, force, wait, host=host, port=port)
        _submit_topology(name, topology_file, topology_jar,
                         env_config, workers, ackers, options, debug,
                         host=host, port=port)
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
    subparser.add_argument('-t', '--time',
                           default=0,
                           type=int,
                           help='Time (in seconds) to keep local cluster '
                                'running. If time <= 0, run indefinitely. '
                                '(default: %(default)s)')
    add_wait(subparser)
    add_workers(subparser)


def main(args):
    """ Submit a Storm topology to Nimbus. """
    resolve_ackers_workers(args)
    submit_topology(name=args.name, env_name=args.environment,
                    workers=args.workers, ackers=args.ackers,
                    options=args.options, force=args.force, debug=args.debug,
                    wait=args.wait, simple_jar=args.simple_jar)

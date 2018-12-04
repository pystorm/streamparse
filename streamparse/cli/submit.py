"""
Submit a Storm topology to Nimbus.
"""

from __future__ import absolute_import, print_function, unicode_literals

import importlib
import os
import sys
import time
from itertools import chain

import simplejson as json
from fabric.api import env
from pkg_resources import parse_version
from six import itervalues

from ..dsl.component import JavaComponentSpec
from ..thrift import ShellComponent, SubmitOptions, TopologyInitialStatus

from ..util import (
    activate_env,
    get_config,
    get_env_config,
    get_nimbus_client,
    get_topology_definition,
    get_topology_from_file,
    nimbus_storm_version,
    set_topology_serializer,
    ssh_tunnel,
    warn,
)
from .common import (
    add_ackers,
    add_config,
    add_debug,
    add_environment,
    add_name,
    add_options,
    add_override_name,
    add_overwrite_virtualenv,
    add_pool_size,
    add_requirements,
    add_timeout,
    add_user,
    add_wait,
    add_workers,
    resolve_options,
)
from .jar import jar_for_deploy
from .kill import _kill_topology
from .list import _list_topologies
from .update_virtualenv import create_or_update_virtualenvs


THRIFT_CHUNK_SIZE = 307200


def get_user_tasks():
    """Get tasks defined in a user's tasks.py and fabfile.py file which is
    assumed to be in the current working directory.

    :returns: a `tuple` (invoke_tasks, fabric_tasks)
    """
    sys.path.insert(0, os.getcwd())
    try:
        user_invoke = importlib.import_module("tasks")
    except ImportError:
        user_invoke = None
    try:
        user_fabric = importlib.import_module("fabfile")
    except ImportError:
        user_fabric = None
    return user_invoke, user_fabric


def is_safe_to_submit(topology_name, nimbus_client):
    """Is topology not in list of current topologies?"""
    topologies = _list_topologies(nimbus_client)
    safe = not any(topology.name == topology_name for topology in topologies)
    return safe


def _kill_existing_topology(topology_name, force, wait, nimbus_client):
    if force and not is_safe_to_submit(topology_name, nimbus_client):
        print('Killing current "{}" topology.'.format(topology_name))
        sys.stdout.flush()
        _kill_topology(topology_name, nimbus_client, wait=wait)
        while not is_safe_to_submit(topology_name, nimbus_client):
            print("Waiting for topology {} to quit...".format(topology_name))
            sys.stdout.flush()
            time.sleep(0.5)
        print("Killed.")
        sys.stdout.flush()


def _submit_topology(
    topology_name,
    topology_class,
    remote_jar_path,
    config,
    env_config,
    nimbus_client,
    options=None,
    active=True,
):
    if options.get("pystorm.log.path"):
        print("Routing Python logging to {}.".format(options["pystorm.log.path"]))
        sys.stdout.flush()

    set_topology_serializer(env_config, config, topology_class)

    # Check if topology name is okay on Storm versions that support that
    if nimbus_storm_version(nimbus_client) >= parse_version("1.1.0"):
        if not nimbus_client.isTopologyNameAllowed(topology_name):
            raise ValueError(
                "Nimbus says {} is an invalid name for a "
                "Storm topology.".format(topology_name)
            )

    print("Submitting {} topology to nimbus...".format(topology_name), end="")
    sys.stdout.flush()
    initial_status = (
        TopologyInitialStatus.ACTIVE if active else TopologyInitialStatus.INACTIVE
    )
    submit_options = SubmitOptions(initial_status=initial_status)
    nimbus_client.submitTopologyWithOpts(
        name=topology_name,
        uploadedJarLocation=remote_jar_path,
        jsonConf=json.dumps(options),
        topology=topology_class.thrift_topology,
        options=submit_options,
    )
    print("done")


def _pre_submit_hooks(topology_name, env_name, env_config, options):
    """Pre-submit hooks for invoke and fabric."""
    user_invoke, user_fabric = get_user_tasks()
    pre_submit_invoke = getattr(user_invoke, "pre_submit", None)
    if callable(pre_submit_invoke):
        pre_submit_invoke(topology_name, env_name, env_config, options)
    pre_submit_fabric = getattr(user_fabric, "pre_submit", None)
    if callable(pre_submit_fabric):
        pre_submit_fabric(topology_name, env_name, env_config, options)


def _post_submit_hooks(topology_name, env_name, env_config, options):
    """Post-submit hooks for invoke and fabric."""
    user_invoke, user_fabric = get_user_tasks()
    post_submit_invoke = getattr(user_invoke, "post_submit", None)
    if callable(post_submit_invoke):
        post_submit_invoke(topology_name, env_name, env_config, options)
    post_submit_fabric = getattr(user_fabric, "post_submit", None)
    if callable(post_submit_fabric):
        post_submit_fabric(topology_name, env_name, env_config, options)


def _upload_jar(nimbus_client, local_path):
    upload_location = nimbus_client.beginFileUpload()
    print(
        "Uploading topology jar {} to assigned location: {}".format(
            local_path, upload_location
        )
    )
    total_bytes = os.path.getsize(local_path)
    bytes_uploaded = 0
    with open(local_path, "rb") as local_jar:
        while True:
            print("Uploaded {}/{} bytes".format(bytes_uploaded, total_bytes), end="\r")
            sys.stdout.flush()
            curr_chunk = local_jar.read(THRIFT_CHUNK_SIZE)
            if not curr_chunk:
                break
            nimbus_client.uploadChunk(upload_location, curr_chunk)
            bytes_uploaded += len(curr_chunk)
        nimbus_client.finishFileUpload(upload_location)
        print("Uploaded {}/{} bytes".format(bytes_uploaded, total_bytes))
        sys.stdout.flush()
    return upload_location


def submit_topology(
    name=None,
    env_name=None,
    options=None,
    force=False,
    wait=None,
    simple_jar=True,
    override_name=None,
    requirements_paths=None,
    local_jar_path=None,
    remote_jar_path=None,
    timeout=None,
    config_file=None,
    overwrite_virtualenv=False,
    user="root",
    active=True,
):
    """Submit a topology to a remote Storm cluster."""
    config = get_config(config_file=config_file)
    name, topology_file = get_topology_definition(name, config_file=config_file)
    env_name, env_config = get_env_config(env_name, config_file=config_file)
    topology_class = get_topology_from_file(topology_file)
    if override_name is None:
        override_name = name
    if remote_jar_path and local_jar_path:
        warn("Ignoring local_jar_path because given remote_jar_path")
        local_jar_path = None

    # Setup the fabric env dictionary
    activate_env(env_name)

    # Handle option conflicts
    options = resolve_options(options, env_config, topology_class, override_name)

    # Check if we need to maintain virtualenv during the process
    use_venv = options.get("use_virtualenv", True)

    # Check if user wants to install virtualenv during the process
    install_venv = options.get("install_virtualenv", use_venv)

    # Run pre_submit actions provided by project
    _pre_submit_hooks(override_name, env_name, env_config, options)

    # If using virtualenv, set it up, and make sure paths are correct in specs
    if use_venv:
        virtualenv_name = options.get("virtualenv_name", override_name)
        if install_venv:
            create_or_update_virtualenvs(
                env_name,
                name,
                options,
                virtualenv_name=virtualenv_name,
                requirements_paths=requirements_paths,
                config_file=config_file,
                overwrite_virtualenv=overwrite_virtualenv,
                user=user,
            )
        streamparse_run_path = "/".join(
            [env.virtualenv_root, virtualenv_name, "bin", "streamparse_run"]
        )
        # Update python paths in bolts
        for thrift_bolt in itervalues(topology_class.thrift_bolts):
            inner_shell = thrift_bolt.bolt_object.shell
            if isinstance(inner_shell, ShellComponent):
                if "streamparse_run" in inner_shell.execution_command:
                    inner_shell.execution_command = streamparse_run_path
        # Update python paths in spouts
        for thrift_spout in itervalues(topology_class.thrift_spouts):
            inner_shell = thrift_spout.spout_object.shell
            if isinstance(inner_shell, ShellComponent):
                if "streamparse_run" in inner_shell.execution_command:
                    inner_shell.execution_command = streamparse_run_path

    # In case we're overriding things, let's save the original name
    options["topology.original_name"] = name

    # Set parallelism based on env_name if necessary
    for thrift_component in chain(
        itervalues(topology_class.thrift_bolts),
        itervalues(topology_class.thrift_spouts),
    ):
        par_hint = thrift_component.common.parallelism_hint
        if isinstance(par_hint, dict):
            thrift_component.common.parallelism_hint = par_hint.get(env_name)

    if local_jar_path:
        print("Using prebuilt JAR: {}".format(local_jar_path))
    elif not remote_jar_path:
        # Check topology for JVM stuff to see if we need to create uber-jar
        if simple_jar:
            simple_jar = not any(
                isinstance(spec, JavaComponentSpec) for spec in topology_class.specs
            )

        # Prepare a JAR that doesn't have Storm dependencies packaged
        local_jar_path = jar_for_deploy(simple_jar=simple_jar)

    if name != override_name:
        print('Deploying "{}" topology with name "{}"...'.format(name, override_name))
    else:
        print('Deploying "{}" topology...'.format(name))
    sys.stdout.flush()
    # Use ssh tunnel with Nimbus if use_ssh_for_nimbus is unspecified or True
    with ssh_tunnel(env_config) as (host, port):
        nimbus_client = get_nimbus_client(
            env_config, host=host, port=port, timeout=timeout
        )
        if remote_jar_path:
            print(
                "Reusing remote JAR on Nimbus server at path: {}".format(
                    remote_jar_path
                )
            )
        else:
            remote_jar_path = _upload_jar(nimbus_client, local_jar_path)
        _kill_existing_topology(override_name, force, wait, nimbus_client)
        _submit_topology(
            override_name,
            topology_class,
            remote_jar_path,
            config,
            env_config,
            nimbus_client,
            options=options,
            active=active,
        )
    _post_submit_hooks(override_name, env_name, env_config, options)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser("submit", description=__doc__, help=main.__doc__)
    subparser.set_defaults(func=main)
    add_ackers(subparser)
    add_config(subparser)
    add_debug(subparser)
    add_environment(subparser)
    subparser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force a topology to submit by killing any "
        "currently running topologies with the same "
        "name.",
    )
    subparser.add_argument(
        "-i",
        "--inactive",
        help="Submit topology as inactive instead of active."
        " This is useful if you are migrating the "
        "topology to a new environment and already "
        "have it running actively in an older one.",
        action="store_false",
        dest="active",
    )
    subparser.add_argument(
        "-j",
        "--local_jar_path",
        help="Path to a prebuilt JAR to upload to Nimbus. "
        "This is useful when you have multiple "
        "topologies that all run out of the same JAR, "
        "or you have manually created the JAR.",
    )
    add_name(subparser)
    add_options(subparser)
    add_override_name(subparser)
    add_overwrite_virtualenv(subparser)
    add_pool_size(subparser)
    add_requirements(subparser)
    subparser.add_argument(
        "-R",
        "--remote_jar_path",
        help="Path to a prebuilt JAR that already exists on "
        "your Nimbus server. This is useful when you "
        "have multiple topologies that all run out of "
        "the same JAR, and you do not want to upload it"
        " multiple times.",
    )
    add_timeout(subparser)
    subparser.add_argument(
        "-u",
        "--uber_jar",
        help="Build an Uber-JAR even if you have no Java "
        "components in your topology.  Useful if you "
        "are providing your own seriailzer class.",
        dest="simple_jar",
        action="store_false",
    )
    add_user(subparser)
    add_wait(subparser)
    add_workers(subparser)


def main(args):
    """ Submit a Storm topology to Nimbus. """
    env.pool_size = args.pool_size
    submit_topology(
        name=args.name,
        env_name=args.environment,
        options=args.options,
        force=args.force,
        wait=args.wait,
        simple_jar=args.simple_jar,
        override_name=args.override_name,
        requirements_paths=args.requirements,
        local_jar_path=args.local_jar_path,
        remote_jar_path=args.remote_jar_path,
        timeout=args.timeout,
        config_file=args.config,
        overwrite_virtualenv=args.overwrite_virtualenv,
        user=args.user,
        active=args.active,
    )

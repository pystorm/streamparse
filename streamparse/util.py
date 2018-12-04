from __future__ import absolute_import, print_function, unicode_literals

import importlib
import os
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from contextlib import contextmanager
from glob import glob
from os.path import join
from random import shuffle
from socket import error as SocketError

import requests
import simplejson as json
from fabric.api import env, hide, local, settings
from fabric.colors import red, yellow
from pkg_resources import parse_version
from texttable import Texttable
from six import iteritems, itervalues
from six.moves.socketserver import UDPServer, TCPServer
from thriftpy.protocol import TBinaryProtocolFactory
from thriftpy.rpc import make_client
from thriftpy.transport import TFramedTransportFactory

from .dsl.topology import Topology, TopologyType
from .thrift import Nimbus


def _port_in_use(port, server_type="tcp"):
    """Check to see whether a given port is already in use on localhost."""
    if server_type == "tcp":
        server = TCPServer
    elif server_type == "udp":
        server = UDPServer
    else:
        raise ValueError("Server type can only be: udp or tcp.")

    try:
        server(("localhost", port), None)
    except SocketError:
        return True

    return False


_active_tunnels = defaultdict(int)


@contextmanager
def ssh_tunnel(env_config, local_port=6627, remote_port=None, quiet=False):
    """Setup an optional ssh_tunnel to Nimbus.

    If use_ssh_for_nimbus is False, no tunnel will be created.
    """
    host, nimbus_port = get_nimbus_host_port(env_config)
    if remote_port is None:
        remote_port = nimbus_port
    if is_ssh_for_nimbus(env_config):
        need_setup = True
        while _port_in_use(local_port):
            if local_port in _active_tunnels:
                active_remote_port = _active_tunnels[local_port]
                if active_remote_port == remote_port:
                    need_setup = False
                    break
            local_port += 1

        if need_setup:
            user = env_config.get("user")
            port = env_config.get("ssh_port")
            if user:
                user_at_host = "{user}@{host}".format(user=user, host=host)
            else:
                user_at_host = host  # Rely on SSH default or config to connect.

            ssh_cmd = [
                "ssh",
                "-NL",
                "{local}:localhost:{remote}".format(
                    local=local_port, remote=remote_port
                ),
                user_at_host,
            ]
            # Specify port if in config
            if port:
                ssh_cmd.insert(-1, "-p")
                ssh_cmd.insert(-1, str(port))

            ssh_proc = subprocess.Popen(ssh_cmd, shell=False)
            # Validate that the tunnel is actually running before yielding
            while not _port_in_use(local_port):
                # Periodically check to see if the ssh command failed and returned a
                # value, then raise an Exception
                if ssh_proc.poll() is not None:
                    raise IOError(
                        'Unable to open ssh tunnel via: "{}"'.format(" ".join(ssh_cmd))
                    )
                time.sleep(0.2)
            if not quiet:
                print(
                    "ssh tunnel to Nimbus {}:{} established.".format(host, remote_port)
                )
            _active_tunnels[local_port] = remote_port
        yield "localhost", local_port
        # Clean up after we exit context
        if need_setup:
            ssh_proc.kill()
        del _active_tunnels[local_port]
    # Do nothing if we're not supposed to use ssh
    else:
        yield host, remote_port


def activate_env(env_name=None, options=None, config_file=None):
    """Activate a particular environment from a streamparse project's
    config.json file and populate fabric's env dictionary with appropriate
    values.

    :param env_name: a `str` corresponding to the key within the config file's
                     "envs" dictionary.
    :param config_file: a `file`-like object that contains the config.json
                        contents. If `None`, we look for a file named
                        ``config.json`` in the working directory.
    """
    env_name, env_config = get_env_config(env_name, config_file=config_file)

    if options and options.get("storm.workers.list"):
        env.storm_workers = options["storm.workers.list"]
    else:
        env.storm_workers = get_storm_workers(env_config)
    env.user = env_config.get("user")
    env.log_path = (
        env_config.get("log_path")
        or env_config.get("log", {}).get("path")
        or get_nimbus_config(env_config).get("storm.log.dir")
    )
    env.virtualenv_root = env_config.get("virtualenv_root") or env_config.get(
        "virtualenv_path"
    )
    env.disable_known_hosts = True
    env.forward_agent = True
    env.use_ssh_config = True
    # fix for config file load issue
    if env_config.get("ssh_password"):
        env.password = env_config.get("ssh_password")


def die(msg, error_code=1):
    print("{}: {}".format(red("error"), msg))
    sys.exit(error_code)


def warn(msg, error_code=1):
    print("{}: {}".format(yellow("warning"), msg))


_config = None


def get_config(config_file=None):
    """
    Parses the config file and returns it as a `dict`.

    :param config_file: a `file`-like object that contains the config.json
                        contents. If `None`, we look for a file named
                        ``config.json`` in the working directory.

    :returns: a `dict` representing the parsed `config_file`.
    """
    global _config
    if _config is not None:
        return _config

    if config_file is None:
        if not os.path.exists("config.json"):
            die(
                "No config.json found. You must run this command inside a "
                "streamparse project directory."
            )

        with open("config.json") as fp:
            config = json.load(fp)
    else:
        config = json.load(config_file)
    _config = config
    return config


def get_topology_definition(topology_name=None, config_file=None):
    """Fetch a topology name and definition file.  If the topology_name is
    None, and there's only one topology definiton listed, we'll select that
    one, otherwise we'll die to avoid ambiguity.

    :param topology_name: a `str`, the topology_name of the topology (without
                          .py extension).
    :param config_file: a `file`-like object that contains the config.json
                        contents. If `None`, we look for a file named
                        ``config.json`` in the working directory.

    :returns: a `tuple` containing (topology_name, topology_file).
    """
    config = get_config(config_file=config_file)
    topology_path = config["topology_specs"]
    if topology_name is None:
        topology_files = glob("{}/*.py".format(topology_path))
        if not topology_files:
            die("No topology definitions are defined in {}.".format(topology_path))
        if len(topology_files) > 1:
            die(
                "Found more than one topology definition file in {specs_dir}. "
                "When more than one topology definition file exists, you must "
                "explicitly specify the topology by name using the -n or "
                "--name flags.".format(specs_dir=topology_path)
            )
        topology_file = topology_files[0]
        topology_name = re.sub(r"(^{}|\.py$)".format(topology_path), "", topology_file)
    else:
        topology_file = "{}.py".format(os.path.join(topology_path, topology_name))
        if not os.path.exists(topology_file):
            die(
                "Topology definition file not found {}. You need to "
                "create a topology definition file first.".format(topology_file)
            )

    return (topology_name, topology_file)


def get_env_config(env_name=None, config_file=None):
    """Fetch an environment name and config object from the config.json file.
    If the name is None and there's only one environment, we'll select the
    first, otherwise we'll die to avoid ambiguity.

    :param config_file: a `file`-like object that contains the config.json
                        contents. If `None`, we look for a file named
                        ``config.json`` in the working directory.

    :returns: a `tuple` containing (env_name, env_config).
    """
    config = get_config(config_file=config_file)
    if env_name is None and len(config["envs"]) == 1:
        env_name = list(config["envs"].keys())[0]
    elif env_name is None and len(config["envs"]) > 1:
        die(
            "Found more than one environment in config.json.  When more than "
            "one environment exists, you must explicitly specify the "
            "environment name via the -e or --environment flags."
        )
    if env_name not in config["envs"]:
        die(
            'Could not find a "{}" in config.json, have you specified one?'.format(
                env_name
            )
        )

    return (env_name, config["envs"][env_name])


def get_nimbus_host_port(env_config):
    """Get the Nimbus server's hostname and port from environment variables
    or from a streamparse project's config file.

    :param env_config: The project's parsed config.
    :type env_config: `dict`

    :returns: (host, port)
    """
    env_config["nimbus"] = os.environ.get("STREAMPARSE_NIMBUS", env_config["nimbus"])

    if not env_config["nimbus"]:
        die("No Nimbus server configured in config.json.")

    if ":" in env_config["nimbus"]:
        host, port = env_config["nimbus"].split(":", 1)
        port = int(port)
    else:
        host = env_config["nimbus"]
        port = 6627
    return (host, port)


def get_nimbus_client(env_config=None, host=None, port=None, timeout=7000):
    """Get a Thrift RPC client for Nimbus given project's config file.

    :param env_config: The project's parsed config.
    :type env_config: `dict`
    :param host: The host to use for Nimbus.  If specified, `env_config` will
                 not be consulted.
    :type host: `str`
    :param port: The port to use for Nimbus.  If specified, `env_config` will
                 not be consulted.
    :type port: `int`
    :param timeout: The time to wait (in milliseconds) for a response from
                    Nimbus.
    :param timeout: `int`

    :returns: a ThriftPy RPC client to use to communicate with Nimbus
    """
    if host is None:
        host, port = get_nimbus_host_port(env_config)
    nimbus_client = make_client(
        Nimbus,
        host=host,
        port=port,
        proto_factory=TBinaryProtocolFactory(),
        trans_factory=TFramedTransportFactory(),
        timeout=timeout,
    )
    return nimbus_client


_storm_workers = {}


def get_storm_workers(env_config):
    """Retrieves list of workers, optionally from nimbus.

    This function will look up the list of current workers from nimbus if
    workers have not been defined in config.json.

    :param env_config: The project's parsed config.
    :type env_config: `dict`

    :returns: List of workers
    """
    nimbus_info = get_nimbus_host_port(env_config)
    if nimbus_info in _storm_workers:
        return _storm_workers[nimbus_info]

    worker_list = env_config.get("workers")
    if not worker_list:
        with ssh_tunnel(env_config) as (host, port):
            nimbus_client = get_nimbus_client(env_config, host=host, port=port)
            cluster_info = nimbus_client.getClusterInfo()
            worker_list = [supervisor.host for supervisor in cluster_info.supervisors]

    _storm_workers[nimbus_info] = worker_list
    return worker_list


_nimbus_configs = {}


def get_nimbus_config(env_config):
    """Retrieves a dict with all the config info stored in Nimbus

    :param env_config: The project's parsed config.
    :type env_config: `dict`

    :returns: dict of Nimbus settings
    """
    nimbus_info = get_nimbus_host_port(env_config)
    if nimbus_info not in _nimbus_configs:
        with ssh_tunnel(env_config) as (host, port):
            nimbus_client = get_nimbus_client(env_config, host=host, port=port)
            nimbus_json = nimbus_client.getNimbusConf()
            nimbus_conf = json.loads(nimbus_json)
        _nimbus_configs[nimbus_info] = nimbus_conf
    return _nimbus_configs[nimbus_info]


def is_ssh_for_nimbus(env_config):
    """Check if we need to use SSH access to Nimbus or not.
    """
    return env_config.get("use_ssh_for_nimbus", True)


def local_storm_version():
    """Get the Storm version available on the users PATH.

    :returns: The Storm library available on the users PATH
    :rtype: pkg_resources.Version
    """
    with hide("running"), settings(warn_only=True):
        cmd = "storm version"
        res = local(cmd, capture=True)
        if not res.succeeded:
            raise RuntimeError(
                "Unable to run '{}'!\nSTDOUT:\n{}"
                "\nSTDERR:\n{}".format(cmd, res.stdout, res.stderr)
            )

    pattern = r"Storm ([0-9.]+)"
    return parse_version(re.findall(pattern, res.stdout, flags=re.MULTILINE)[0])


def nimbus_storm_version(nimbus_client):
    """Get the Storm version that Nimbus is reporting, if it's reporting it.

    :returns: Storm version that Nimbus is reporting, if it's reporting it.
              Will return `LegacyVersion('')` if it's not reporting anything.
    :rtype: pkg_resources.Version
    """
    version = parse_version("")
    nimbuses = nimbus_client.getClusterInfo().nimbuses
    if nimbuses is not None:
        for nimbus in nimbuses:
            if nimbus.version != "VERSION_NOT_PROVIDED":
                version = parse_version(nimbus.version)
                break
    return version


def storm_lib_version():
    """Get the Storm library version being used by Leiningen.

    :returns: The Storm library version specified in project.clj
    :rtype: pkg_resources.Version
    """
    with hide("running"), settings(warn_only=True):
        cmd = "lein deps :tree"
        res = local(cmd, capture=True)
        if not res.succeeded:
            raise RuntimeError(
                "Unable to run '{}'!\nSTDOUT:\n{}"
                "\nSTDERR:\n{}".format(cmd, res.stdout, res.stderr)
            )
    deps_tree = res.stdout
    pattern = r'\[org\.apache\.storm/storm-core "([^"]+)"\]'
    versions = set(re.findall(pattern, deps_tree))

    if len(versions) > 1:
        raise RuntimeError("Multiple Storm Versions Detected.")
    elif len(versions) == 0:
        raise RuntimeError("No Storm version specified in project.clj " "dependencies.")
    else:
        return parse_version(versions.pop())


def get_ui_jsons(env_name, api_paths, config_file=None):
    """Take env_name as a string and api_paths that should
    be a list of strings like '/api/v1/topology/summary'
    """
    _, env_config = get_env_config(env_name, config_file=config_file)
    host, _ = get_nimbus_host_port(env_config)
    # TODO: Get remote_ui_port from storm?
    remote_ui_port = env_config.get("ui.port", 8080)
    # SSH tunnel can take a while to close. Check multiples if necessary.
    local_ports = list(range(8081, 8090))
    shuffle(local_ports)
    for local_port in local_ports:
        try:
            data = {}
            with ssh_tunnel(
                env_config, local_port=local_port, remote_port=remote_ui_port
            ) as (host, local_port):
                for api_path in api_paths:
                    url = "http://{}:{}{}".format(host, local_port, api_path)
                    r = requests.get(url)
                    data[api_path] = r.json()
                    error = data[api_path].get("error")
                    if error:
                        error_msg = data[api_path].get("errorMessage")
                        raise RuntimeError(
                            "Received bad response from {}: "
                            "{}\n{}".format(url, error, error_msg)
                        )
            return data
        except Exception as e:
            if "already in use" in str(e):
                continue
            raise
    raise RuntimeError("Cannot find local port for SSH tunnel to Storm Head.")


def get_ui_json(env_name, api_path, config_file=None):
    """Take env_name as a string and api_path that should
    be a string like '/api/v1/topology/summary'
    """
    return get_ui_jsons(env_name, [api_path], config_file=config_file)[api_path]


def prepare_topology():
    """Prepare a topology for JAR creation"""
    resources_dir = join("_resources", "resources")
    if os.path.isdir(resources_dir):
        shutil.rmtree(resources_dir)
    if os.path.exists("src"):
        shutil.copytree("src", resources_dir)
    else:
        raise FileNotFoundError('Your project must have a "src" directory.')


def _get_file_names_command(path, patterns):
    """Given a list of bash `find` patterns, return a string for the
    bash command that will find those pystorm log files
    """
    if path is None:
        raise ValueError("path cannot be None")
    patterns = "' -o -type f -wholename '".join(patterns)
    return (
        "cd {path} && " "find . -maxdepth 4 -type f -wholename '{patterns}'"
    ).format(path=path, patterns=patterns)


def get_logfiles_cmd(
    topology_name=None,
    pattern=None,
    include_worker_logs=True,
    is_old_storm=False,
    include_all_artifacts=False,
):
    """ Returns a string representing a command to run on the Storm workers that
    will yield all of the logfiles for the given topology that meet the given
    pattern (if specified).
    """
    log_name_patterns = ["*{topo_name}*".format(topo_name=topology_name)]
    if not include_all_artifacts:
        log_name_patterns[0] += ".log"
    # The worker logs are separated by topology in Storm 1.0+, so no need to do
    # this except on old versions of Storm
    if not is_old_storm:
        include_worker_logs = False
    # list log files found
    if include_worker_logs:
        log_name_patterns.extend(["worker*", "supervisor*", "access*", "metrics*"])
    if env.log_path is None:
        raise ValueError(
            "Cannot find log files if you do not set `log_path` "
            "or the `path` key in the `log` dict for your "
            "environment in your config.json."
        )
    ls_cmd = _get_file_names_command(env.log_path, log_name_patterns)
    if pattern is not None:
        ls_cmd += " | egrep '{pattern}'".format(pattern=pattern)
    return ls_cmd


def print_stats_table(
    header, data, columns, default_alignment="l", custom_alignment=None
):
    """Print out a list of dictionaries (or objects) as a table.

    If given a list of objects, will print out the contents of objects'
    `__dict__` attributes.

    :param header: Header that will be printed above table.
    :type header:  `str`
    :param data:   List of dictionaries (or objects )
    """
    print("# %s" % header)
    table = Texttable(max_width=115)
    table.header(columns)
    table.set_cols_align(default_alignment * len(columns))
    if not isinstance(data, list):
        data = [data]
    for row in data:
        # Treat all non-list/tuple objects like dicts to make life easier
        if not isinstance(row, (list, tuple, dict)):
            row = vars(row)
        if isinstance(row, dict):
            row = [row.get(key, "MISSING") for key in columns]
        table.add_row(row)
    if custom_alignment:
        table.set_cols_align(
            [custom_alignment.get(column, default_alignment) for column in columns]
        )
    print(table.draw())


def get_topology_from_file(topology_file):
    """
    Given a filename for a topology, import the topology and return the class
    """
    topology_dir, mod_name = os.path.split(topology_file)
    # Remove .py extension before trying to import
    mod_name = mod_name[:-3]
    sys.path.append(os.path.join(topology_dir, "..", "src"))
    sys.path.append(topology_dir)
    mod = importlib.import_module(mod_name)
    for attr in mod.__dict__.values():
        if isinstance(attr, TopologyType) and attr != Topology:
            topology_class = attr
            break
    else:
        raise ValueError("Could not find topology subclass in topology module.")
    return topology_class


def set_topology_serializer(env_config, config, topology_class):
    """Go through the components in a `Topology` and set the serializer.

    This is necessary because the `Topology` class has no information about the
    user-specified serializer, but it needs to be passed as an argument to
    ``streamparse_run``.
    """
    serializer = env_config.get("serializer", config.get("serializer", None))
    if serializer is not None:
        # Set serializer arg in bolts
        for thrift_bolt in itervalues(topology_class.thrift_bolts):
            inner_shell = thrift_bolt.bolt_object.shell
            if inner_shell is not None:
                inner_shell.script = "-s {} {}".format(serializer, inner_shell.script)
        # Set serializer arg in spouts
        for thrift_spout in itervalues(topology_class.thrift_spouts):
            inner_shell = thrift_spout.spout_object.shell
            if inner_shell is not None:
                inner_shell.script = "-s {} {}".format(serializer, inner_shell.script)

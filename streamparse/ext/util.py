from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import re
import sys
from glob import glob

from fabric.colors import red

from ..decorators import memoized


def die(msg, error_code=1):
    print("{}: {}".format(red("error"), msg))
    sys.exit(error_code)


@memoized
def get_config():
    if not os.path.exists("config.json"):
        die("No config.json found. You must run this command inside a "
            "streamparse project directory.")

    with open("config.json") as fp:
        config = json.load(fp)
    return config


def get_topology_definition(topology_name=None):
    """Fetch a topology name and definition file.  If the topology_name is
    None, and there's only one topology definiton listed, we'll select that
    one, otherwise we'll die to avoid ambiguity.

    :param topology_name: a `str`, the topology_name of the topology (without .clj extension).
    :returns: a `tuple` containing (topology_topology_name, topology_file).
    """
    config = get_config()
    topology_path = config["topology_specs"]
    if topology_name is None:
        topology_files = glob("{}/*.clj".format(topology_path))
        if not topology_files:
            die("No topology definitions are defined in {}."
                .format(topology_path))
        if len(topology_files) > 1:
            die("Found more than one topology definition file in {specs_dir}. "
                "When more than one topology definition file exists, you must "
                "explicitly specify the topology by name using the -n or "
                "--name flags.".format(specs_dir=topology_path))
        topology_file = topology_files[0]
        topology_name = re.sub(r'(^{}|\.clj$)'.format(topology_path), '', topology_file)
    else:
        topology_file = "{}.clj".format(os.path.join(topology_path, topology_name))
        if not os.path.exists(topology_file):
            die("Topology definition file not found {}. You need to "
                "create a topology definition file first."
                .format(topology_file))

    return (topology_name, topology_file)


def get_env_config(env_name=None):
    """Fetch an environment name and config object from the config.json file.
    If the name is None and there's only one environment, we'll select the
    first, otherwise we'll die to avoid ambiguity.

    :returns: a `tuple` containing (env_name, env_config).
    """
    config = get_config()
    if env_name is None and len(config["envs"]) == 1:
        env_name = list(config["envs"].keys())[0]
    elif env_name is None and len(config["envs"]) > 1:
        die("Found more than one environment in config.json. "
            "When more than one environment exists, you must "
            "explicitly specify the environment name via the "
            "-e or --environment flags.")
    if env_name not in config["envs"]:
        die("Could not find a \"{}\" in config.json, have you specified one?"
            .format(env_name))

    return (env_name, config["envs"][env_name])


def get_nimbus_for_env_config(env_config):
    """Get the Nimbus server's hostname and port from a streamparse project's
    config file.
    """
    if not env_config["nimbus"]:
        die("No Nimbus server configured in config.json.")

    if ":" in env_config["nimbus"]:
        host, port = env_config["nimbus"].split(":", 1)
        port = int(port)
    else:
        host = env_config["nimbus"]
        port = 6627

    return (host, port)

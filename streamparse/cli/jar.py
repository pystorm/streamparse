"""
Create a JAR that can be used to deploy a topology to Storm.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import shutil
import sys
import subprocess

from ..util import prepare_topology
from .common import add_simple_jar


def jar_for_deploy(simple_jar=False):
    """ Build a jar to use for deploying the topology. """
    # Create _resources folder which will contain Python code in JAR
    prepare_topology()
    # Use Leiningen to clean up and build JAR
    jar_type = "JAR" if simple_jar else "Uber-JAR"
    print("Cleaning from prior builds...")
    sys.stdout.flush()
    try:
        subprocess.check_output(["lein clean"], shell=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Unable to run 'lein clean'!\nSTDERR:\n{}".format(exc.output))

    print("Creating topology {}...".format(jar_type))
    sys.stdout.flush()
    cmd = "lein jar" if simple_jar else "lein uberjar"

    try:
        output = subprocess.check_output([cmd], shell=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Unable to run '{}'!\nSTDERR:\n{}".format(cmd, exc.output))

    # XXX: This will fail if more than one JAR is built
    lines = output.splitlines()
    for line in lines:
        line = line.strip()
        if not line.startswith("Created"):
            continue
        line = line.replace("Created ", "")
        # != is XOR
        if simple_jar != line.endswith("standalone.jar"):
            jar = line
            break
    else:
        raise RuntimeError("Failed to find JAR in '{}' output\STDOUT:\n{}".format(cmd, output))
    print("{} created: {}".format(jar_type, jar))
    sys.stdout.flush()
    print('Removing _resources temporary directory...', end='')
    sys.stdout.flush()
    resources_dir = os.path.join("_resources", "resources")
    if os.path.isdir(resources_dir):
        shutil.rmtree(resources_dir)
    print('done')
    return jar


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('jar',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_simple_jar(subparser)


def main(args):
    """ Create a deployable JAR for a topology. """
    jar_for_deploy(simple_jar=args.simple_jar)

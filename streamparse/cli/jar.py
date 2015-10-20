"""
Create a JAR that can be used to deploy a topology to Storm.
"""

from __future__ import absolute_import, print_function, unicode_literals

import sys

from invoke import run

from .common import add_simple_jar
from ..util import prepare_topology


def jar_for_deploy(simple_jar=False):
    """ Build a jar to use for deploying the topology. """
    # Create _resources folder which will contain Python code in JAR
    prepare_topology()
    # Use Leiningen to clean up and build JAR
    jar_type = "JAR" if simple_jar else "Uber-JAR"
    print("Cleaning from prior builds...")
    sys.stdout.flush()
    res = run("lein clean", hide="stdout")
    if not res.ok:
        raise RuntimeError("Unable to run 'lein clean'!\nSTDOUT:\n{}"
                           "\nSTDERR:\n{}".format(res.stdout, res.stderr))
    print("Creating topology {}...".format(jar_type))
    sys.stdout.flush()
    cmd = "lein jar" if simple_jar else "lein uberjar"
    res = run(cmd, hide="stdout")
    if not res.ok:
        raise RuntimeError("Unable to run '{}'!\nSTDOUT:\n{}"
                           "\nSTDERR:\n{}".format(cmd, res.stdout, res.stderr))
    # XXX: This will fail if more than one JAR is built
    lines = res.stdout.splitlines()
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
        raise RuntimeError("Failed to find JAR in '{}' output\STDOUT:\n{}"
                           "STDERR:\n{}".format(cmd, res.stdout, res.stderr))
    print("{} created: {}".format(jar_type, jar))
    sys.stdout.flush()
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

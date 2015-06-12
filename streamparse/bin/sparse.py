from __future__ import absolute_import
import os
import sys
import pkgutil
import argparse
import importlib

###############################################################################
# This module provides the base sparse command and a load hook for dynamically
# adding other subcommands.  The "load_suparsers" function searches for modules
# in the streamparse/bin directory that have a "subparser_hook" method. The
# "subparser_hook" accepts a the sparse subparsers object and adds it's
# subparser as needed.
###############################################################################

def load_suparsers(subparsers):
    """
    searches modules in streamparse/bin for a 'subparser_hook' method and calls
    the 'subparser_hook' method on the sparse subparsers object.
    """
    for importer, package_name, _ in pkgutil.iter_modules([
        os.path.dirname(__file__)
    ]):
        try:
            mod_name = __name__.replace(
                __file__.rsplit('/')[-1].split('.')[0], package_name
            )
            module   = __import__(mod_name, fromlist=['subparser_hook'])
        except ImportError:
            # if we can't immport it we skip trying to add the subparser
            pass
        # check for the subparser hook
        if hasattr(module, 'subparser_hook'):
            module.subparser_hook(subparsers)


def main():
    """main entry point for sparse"""
    parser = argparse.ArgumentParser(
        prog        = "sparse",
        description = "sparse: manage streamparse clusters.",
        epilog      = """sparse provides a front-end to
        streamparse, a framework for creating Python projects for running,
        debugging, and submitting computation topologies against real-time
        streams, using Apache Storm. It requires java and lein (Clojure
        build tool) to be on your $PATH, and uses lein and Clojure under the
        hood for JVM/Thrift interop.
        """
    )

    subparsers = parser.add_subparsers()
    load_suparsers(subparsers)
    args = parser.parse_args()

    ### http://grokbase.com/t/python/python-bugs-list/12arsq9ayf/issue16308-undocumented-behaviour-change-in-argparse-from-3-2-3-to-3-3-0
    try:
        getattr(args, "func")
        args.func(args)
    # python3.3+ argparse changes
    except AttributeError:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()

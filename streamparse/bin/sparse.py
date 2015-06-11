from __future__ import absolute_import
import os
import sys
import pkgutil
import argparse

###############################################################################
# This module provides the base sparse command and a load hook for dynamically
# adding other subcommands.  The "load_suparsers" function searches for modules
# in the streamparse/bin directory that have a "subparser_hook" method. The
# "subparser_hook" accepts a the sparse subparsers object and adds it's
# subparser as needed.
###############################################################################

def load_suparsers(dirname, subparsers):
    """
    searches modules in streamparse/bin for a 'subparser_hook' method and calls
    the 'subparser_hook' method on the sparse subparsers object.
    """
    for importer, package_name, _ in pkgutil.iter_modules([dirname]):
        full_package_name = '%s.%s' % (dirname, package_name)
        if  full_package_name not in sys.modules:
            # skip this package
            if package_name in os.path.basename(__file__):
                continue
            module = importer.find_module(package_name).load_module(
                full_package_name
            )
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
    load_suparsers(os.path.dirname(__file__), subparsers)
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()

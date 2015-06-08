from __future__ import absolute_import
import os
import sys
import pkgutil
import argparse


def load_suparsers(dirname, subparsers):
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
    parser = argparse.ArgumentParser(
        prog        = "sparse",
        description = "sparse: manage streamparse clusters.",
        epilog      = """sparse provides a front-end to
        streamparse, a framework for creating Python projects for running,
        debugging, and submitting computation topologies against real-time
        streams, using Apache Storm. It requires the java and lein (Clojure
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

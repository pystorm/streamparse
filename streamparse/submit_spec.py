"""
Helper script for starting up topologies.
"""

import argparse
import importlib

from .util import get_nimbus_client


def main():
    """main entry point for Python topologies"""
    parser = argparse.ArgumentParser(description='Submit a Python DSL topology',
                                     epilog='This is internal to streamparse '
                                            'and is used to submit topology '
                                            'specs after JARs have been '
                                            'uploaded.  It is called '
                                            'automatically by `storm shell`, '
                                            'which is called by `sparse '
                                            'submit`.')
    parser.add_argument('host', help='The host for Nimbus.')
    parser.add_argument('port', help='The port for Nimbus.')
    parser.add_argument('jar', help='The JAR path on the server.')
    parser.add_argument('target_class', help='The topology class to submit.')
    args = parser.parse_args()
    mod_name, cls_name = args.target_class.rsplit('.', 1)
    mod = importlib.import_module(mod_name)
    topology_class = getattr(mod, cls_name)
    nimbus_client = get_nimbus_client(host=args.host, port=args.port)
    nimbus_client.submitTopology(name=topology_class.__name__,
                                 uploadedJarLocation=args.jar,
                                 jsonConf=None,
                                 topology=topology_class._topology)


if __name__ == '__main__':
    main()

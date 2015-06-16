"""
Display uptime for workers in running Storm topologies.
"""

from __future__ import absolute_import, print_function

from pkg_resources import parse_version
from prettytable import PrettyTable

from .common import add_environment
from ..util import get_ui_json, storm_lib_version


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('worker_uptime',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_environment(subparser)


def display_worker_uptime(env_name):
    topology_summary = '/api/v1/topology/summary'
    topology_detail = '/api/v1/topology/{topology}'
    component = '/api/v1/topology/{topology}/component/{component}'
    topo_summary_json = get_ui_json(env_name, topology_summary)
    topology_ids = [x['id'] for x in topo_summary_json['topologies']]
    worker_stats = []

    for topology in topology_ids:
        topology_detail_json = get_ui_json(env_name,
                                           topology_detail.format(topology=topology))
        spouts = [x['spoutId'] for x in topology_detail_json['spouts']]
        bolts = [x['boltId'] for x in topology_detail_json['bolts']]
        for comp in spouts + bolts:
            comp_detail = get_ui_json(env_name,
                                      component.format(topology=topology,
                                                       component=comp))
            worker_stats += [(worker['host'], worker['id'], worker['uptime'],
                              worker['workerLogLink']) for worker in
                             comp_detail['executorStats']]
    worker_stats = sorted(set(worker_stats))

    print("# Worker Stats")
    table = PrettyTable(["Host", "Worker ID", "Uptime", "Log URL"])
    table.align = 'l'
    table.align['Uptime'] = 'r'
    for row in worker_stats:
        table.add_row(row)
    print(table)
    print()


def main(args):
    """ Display uptime for Storm workers. """
    storm_version = storm_lib_version()
    if storm_version >= parse_version('0.9.2-incubating'):
        display_worker_uptime(args.environment)
    else:
        print("ERROR: Storm {0} does not support this command."
              .format(storm_version))

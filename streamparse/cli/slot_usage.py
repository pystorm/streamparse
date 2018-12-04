"""
Display slots used by every topology on the cluster
"""

from __future__ import absolute_import, print_function

from collections import Counter, defaultdict

from pkg_resources import parse_version
from six import iteritems

from .common import add_config, add_environment
from ..util import get_ui_json, get_ui_jsons, print_stats_table, storm_lib_version


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser(
        "slot_usage", description=__doc__, help=main.__doc__
    )
    subparser.set_defaults(func=main)
    add_config(subparser)
    add_environment(subparser)


def display_slot_usage(env_name, config_file=None):
    print(
        "Querying Storm UI REST service for slot usage stats (this can take a while)..."
    )
    topology_summary_path = "/api/v1/topology/summary"
    topology_detail_path = "/api/v1/topology/{topology}"
    component_path = "/api/v1/topology/{topology}/component/{component}"
    topo_summary_json = get_ui_json(
        env_name, topology_summary_path, config_file=config_file
    )
    topology_ids = [x["id"] for x in topo_summary_json["topologies"]]
    # Keep track of the number of workers used by each topology on each machine
    topology_worker_ports = defaultdict(lambda: defaultdict(set))
    topology_executor_counts = defaultdict(Counter)
    topology_names = set()
    topology_components = dict()
    topology_detail_jsons = get_ui_jsons(
        env_name,
        (topology_detail_path.format(topology=topology) for topology in topology_ids),
        config_file=config_file,
    )

    for topology in topology_ids:
        topology_detail_json = topology_detail_jsons[
            topology_detail_path.format(topology=topology)
        ]
        spouts = [x["spoutId"] for x in topology_detail_json["spouts"]]
        bolts = [x["boltId"] for x in topology_detail_json["bolts"]]
        topology_components[topology] = spouts + bolts

    comp_details = get_ui_jsons(
        env_name,
        (
            component_path.format(topology=topology, component=comp)
            for topology, comp_list in iteritems(topology_components)
            for comp in comp_list
        ),
        config_file=config_file,
    )

    for request_url, comp_detail in iteritems(comp_details):
        topology = request_url.split("/")[4]
        topology_detail_json = topology_detail_jsons[
            topology_detail_path.format(topology=topology)
        ]
        for worker in comp_detail["executorStats"]:
            topology_worker_ports[worker["host"]][topology_detail_json["name"]].add(
                worker["port"]
            )
            topology_executor_counts[worker["host"]][topology_detail_json["name"]] += 1
            topology_names.add(topology_detail_json["name"])

    topology_names = sorted(topology_names)
    columns = ["Host"] + topology_names
    rows = [
        (
            [host]
            + [
                "{} ({})".format(
                    len(host_dict.get(topology, set())),
                    topology_executor_counts[host][topology],
                )
                for topology in topology_names
            ]
        )
        for host, host_dict in sorted(iteritems(topology_worker_ports))
    ]
    print_stats_table("Slot (and Executor) Counts by Topology", rows, columns)


def main(args):
    """ Display slots used by every topology on the cluster. """
    storm_version = storm_lib_version()
    if storm_version >= parse_version("0.9.2-incubating"):
        display_slot_usage(args.environment)
    else:
        print("ERROR: Storm {0} does not support this command.".format(storm_version))

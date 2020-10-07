"""
Display uptime for workers in running Storm topologies.
"""

from pkg_resources import parse_version

from .common import add_config, add_environment
from ..util import get_ui_json, get_ui_jsons, print_stats_table, storm_lib_version


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser(
        "worker_uptime", description=__doc__, help=main.__doc__
    )
    subparser.set_defaults(func=main)
    add_config(subparser)
    add_environment(subparser)


def display_worker_uptime(env_name, config_file=None):
    topology_summary_path = "/api/v1/topology/summary"
    topology_detail_path = "/api/v1/topology/{topology}"
    component_path = "/api/v1/topology/{topology}/component/{component}"
    topo_summary_json = get_ui_json(
        env_name, topology_summary_path, config_file=config_file
    )
    topology_ids = [x["id"] for x in topo_summary_json["topologies"]]
    topology_components = dict()
    worker_stats = []
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
            for topology, comp_list in topology_components.items()
            for comp in comp_list
        ),
        config_file=config_file,
    )

    for comp_detail in comp_details.values():
        worker_stats += [
            (worker["host"], worker["id"], worker["uptime"], worker["workerLogLink"])
            for worker in comp_detail["executorStats"]
        ]
    worker_stats = sorted(set(worker_stats))

    print_stats_table(
        "Worker Stats",
        worker_stats,
        ["Host", "Worker ID", "Uptime", "Log URL"],
        custom_alignment={"Uptime": "r"},
    )


def main(args):
    """ Display uptime for Storm workers. """
    storm_version = storm_lib_version()
    if storm_version >= parse_version("0.9.2-incubating"):
        display_worker_uptime(args.environment, config_file=args.config)
    else:
        print(f"ERROR: Storm {storm_version} does not support this command.")

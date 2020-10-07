"""
Display stats about running Storm topologies.
"""

import sys
from itertools import chain

from pkg_resources import parse_version

from ..util import (
    get_env_config,
    get_ui_json,
    get_ui_jsons,
    print_stats_table,
    storm_lib_version,
)
from .common import add_config, add_environment, add_name


def display_stats(
    env_name,
    topology_name=None,
    component_name=None,
    all_components=None,
    config_file=None,
):
    env_name = env_name
    if topology_name and all_components:
        _print_all_components(env_name, topology_name, config_file=config_file)
    elif topology_name and component_name:
        _print_component_status(
            env_name, topology_name, component_name, config_file=config_file
        )
    elif topology_name:
        _print_topology_status(env_name, topology_name, config_file=config_file)
    else:
        _print_cluster_status(env_name, config_file=config_file)


def _print_cluster_status(env_name, config_file=None):
    jsons = get_ui_jsons(
        env_name,
        [
            "/api/v1/cluster/summary",
            "/api/v1/topology/summary",
            "/api/v1/supervisor/summary",
        ],
        config_file=config_file,
    )
    # Print Cluster Summary
    ui_cluster_summary = jsons["/api/v1/cluster/summary"]
    columns = [
        "stormVersion",
        "nimbusUptime",
        "supervisors",
        "slotsTotal",
        "slotsUsed",
        "slotsFree",
        "executorsTotal",
        "tasksTotal",
    ]
    print_stats_table("Cluster summary", ui_cluster_summary, columns, "r")
    # Print Topologies Summary
    ui_topologies_summary = jsons["/api/v1/topology/summary"]
    columns = [
        "name",
        "id",
        "status",
        "uptime",
        "workersTotal",
        "executorsTotal",
        "tasksTotal",
    ]
    print_stats_table(
        "Topology summary", ui_topologies_summary["topologies"], columns, "r"
    )
    # Print Supervisor Summary
    ui_supervisor_summary = jsons["/api/v1/supervisor/summary"]
    columns = ["id", "host", "uptime", "slotsTotal", "slotsUsed"]
    print_stats_table(
        "Supervisor summary",
        ui_supervisor_summary["supervisors"],
        columns,
        "r",
        {"host": "l", "uptime": "l"},
    )


def _get_topology_ui_detail(env_name, topology_name, config_file=None):
    env_name = get_env_config(env_name, config_file=config_file)[0]
    topology_id = _get_topology_id(env_name, topology_name)
    detail_url = f"/api/v1/topology/{topology_id}"
    detail = get_ui_json(env_name, detail_url, config_file=config_file)
    return detail


def _print_topology_status(env_name, topology_name, config_file=None):
    ui_detail = _get_topology_ui_detail(
        env_name, topology_name, config_file=config_file
    )
    # Print topology summary
    columns = [
        "name",
        "id",
        "status",
        "uptime",
        "workersTotal",
        "executorsTotal",
        "tasksTotal",
    ]
    print_stats_table("Topology summary", ui_detail, columns, "r")
    # Print topology stats
    columns = [
        "windowPretty",
        "emitted",
        "transferred",
        "completeLatency",
        "acked",
        "failed",
    ]
    print_stats_table("Topology stats", ui_detail["topologyStats"], columns, "r")
    # Print spouts
    if ui_detail.get("spouts"):
        columns = [
            "spoutId",
            "emitted",
            "transferred",
            "completeLatency",
            "acked",
            "failed",
        ]
        print_stats_table(
            "Spouts (All time)", ui_detail["spouts"], columns, "r", {"spoutId": "l"}
        )

    columns = [
        "boltId",
        "executors",
        "tasks",
        "emitted",
        "transferred",
        "capacity",
        "executeLatency",
        "executed",
        "processLatency",
        "acked",
        "failed",
        "lastError",
    ]
    print_stats_table(
        "Bolt (All time)", ui_detail["bolts"], columns, "r", {"boltId": "l"}
    )


def _get_component_ui_detail(
    env_name, topology_name, component_names, config_file=None
):
    if isinstance(component_names, str):
        component_names = [component_names]
    env_name = get_env_config(env_name, config_file=config_file)[0]
    topology_id = _get_topology_id(env_name, topology_name, config_file=config_file)
    base_url = "/api/v1/topology/%s/component/%s"
    detail_urls = [base_url % (topology_id, name) for name in component_names]
    detail = get_ui_jsons(env_name, detail_urls, config_file=config_file)
    if len(detail) == 1:
        return list(detail.values())[0]
    else:
        return detail


def _print_all_components(env_name, topology_name, config_file=None):
    topology_ui_detail = _get_topology_ui_detail(env_name, topology_name)
    spouts = map(lambda spout: (spout["spoutId"], topology_ui_detail.get("spouts", {})))
    bolts = map(lambda spout: (spout["boltId"], topology_ui_detail.get("bolts", {})))
    ui_details = _get_component_ui_detail(
        env_name, topology_name, chain(spouts, bolts), config_file=config_file
    )
    names_and_keys = zip(
        map(lambda ui_detail: (ui_detail["name"], ui_details.values())),
        ui_details.keys(),
    )
    for component_name, key in names_and_keys:
        _print_component_status(
            env_name,
            topology_name,
            component_name,
            ui_details[key],
            config_file=config_file,
        )


def _print_component_status(
    env_name, topology_name, component_name, ui_detail=None, config_file=None
):
    if not ui_detail:
        ui_detail = _get_component_ui_detail(
            env_name, topology_name, component_name, config_file=config_file
        )
    _print_component_summary(ui_detail)
    if ui_detail.get("componentType") == "spout":
        _print_spout_stats(ui_detail)
        _print_spout_output_stats(ui_detail)
        _print_spout_executors(ui_detail)
    elif ui_detail.get("componentType") == "bolt":
        _print_bolt_stats(ui_detail)
        _print_input_stats(ui_detail)
        _print_bolt_output_stats(ui_detail)


def _print_component_summary(ui_detail):
    columns = ["id", "name", "executors", "tasks"]
    print_stats_table("Component summary", ui_detail, columns, "r")


def _print_bolt_stats(ui_detail):
    columns = [
        "windowPretty",
        "emitted",
        "transferred",
        "executeLatency",
        "executed",
        "processLatency",
        "acked",
        "failed",
    ]

    print_stats_table(
        "Bolt stats", ui_detail["boltStats"], columns, "r", {"windowPretty": "l"}
    )


def _print_input_stats(ui_detail):
    columns = [
        "component",
        "stream",
        "executeLatency",
        "processLatency",
        "executed",
        "acked",
        "failed",
    ]
    if ui_detail["inputStats"]:
        print_stats_table(
            "Input stats (All time)",
            ui_detail["inputStats"],
            columns,
            "r",
            {"component": "l"},
        )


def _print_bolt_output_stats(ui_detail):
    if ui_detail["outputStats"]:
        columns = ["stream", "emitted", "transferred"]
        print_stats_table(
            "Output stats (All time)",
            ui_detail["outputStats"],
            columns,
            "r",
            {"stream": "l"},
        )


def _print_spout_stats(ui_detail):
    columns = [
        "windowPretty",
        "emitted",
        "transferred",
        "completeLatency",
        "acked",
        "failed",
    ]
    data = ui_detail["spoutSummary"][-1].copy()
    print_stats_table("Spout stats", data, columns, "r", {"windowPretty": "l"})


def _print_spout_output_stats(ui_detail):
    columns = ["stream", "emitted", "transferred", "completeLatency", "acked", "failed"]
    print_stats_table(
        "Output stats (All time)",
        ui_detail["outputStats"],
        columns,
        "r",
        {"stream": "l"},
    )


def _print_spout_executors(ui_detail):
    columns = [
        "id",
        "uptime",
        "host",
        "port",
        "emitted",
        "transferred",
        "completeLatency",
        "acked",
        "failed",
    ]
    print_stats_table(
        "Executors (All time)", ui_detail["executorStats"], columns, "r", {"host": "l"}
    )


def _get_topology_id(env_name, topology_name, config_file=None):
    """Get toplogy ID from summary json provided by UI api"""
    summary_url = "/api/v1/topology/summary"
    topology_summary = get_ui_json(env_name, summary_url, config_file=config_file)
    for topology in topology_summary["topologies"]:
        if topology_name == topology["name"]:
            return topology["id"]


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser("stats", description=__doc__, help=main.__doc__)
    subparser.set_defaults(func=main)
    subparser.add_argument("--all", action="store_true", help="All available stats.")
    subparser.add_argument(
        "-c",
        "--component",
        help="Topology component (bolt/spout) name as "
        "specified in Clojure topology specification",
    )
    add_config(subparser)
    add_environment(subparser)
    add_name(subparser)


def main(args):
    """ Display stats about running Storm topologies. """
    storm_version = storm_lib_version()
    if storm_version >= parse_version("0.9.2-incubating"):
        display_stats(
            args.environment,
            topology_name=args.name,
            component_name=args.component,
            all_components=args.all,
            config_file=args.config,
        )
    else:
        print(f"ERROR: Storm {storm_version} does not support this command.")
        sys.stdout.flush()

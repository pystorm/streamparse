"""streamparse.ext.invoke

invoke tasks that are imported into a project's task.py.

Should be used like this::

    from invoke import task, run
    from streamparse.ext.invoke import *

    # your other tasks
"""
from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import shutil
import sys
import time
import requests
from operator import itemgetter
from prettytable import PrettyTable
from random import shuffle

from invoke import run, task
from itertools import chain
from pkg_resources import parse_version
from six import iteritems, string_types

from ..contextmanagers import ssh_tunnel
from .util import (get_env_config, get_topology_definition,
                   get_nimbus_for_env_config, get_config,
                   is_ssh_for_nimbus)
from .fabric import activate_env, create_or_update_virtualenvs, tail_logs


__all__ = ["list_topologies", "kill_topology", "run_local_topology",
           "submit_topology", "tail_topology"]

# TODO: remove boilerplate get_env_config, get_nimbus_for_env_config...
# from all these with something like
# @task("setup")


def storm_lib_version():
    """Get the Storm library version being used by Leiningen and Streamparse.

    :returns: The Storm library version specified in project.clj
    :rtype: pkg_resources.Version
    """
    deps_tree = run("lein deps :tree", hide=True).stdout
    pattern = r'\[org\.apache\.storm/storm-core "([^"]+)"\]'
    versions = set(re.findall(pattern, deps_tree))

    if len(versions) > 1:
        raise RuntimeError("Multiple Storm Versions Detected.")
    elif len(versions) == 0:
        raise RuntimeError("No Storm version specified in project.clj dependencies.")
    else:
        return parse_version(versions.pop())


def get_user_tasks():
    """Get tasks defined in a user's tasks.py and fabric.py file which is
    assumed to be in the current working directory.

    :returns: tuple invoke_tasks, fabric_tasks
    """
    try:
        sys.path.insert(0, os.getcwd())
        import tasks as user_invoke
        import fabfile as user_fabric
        return user_invoke, user_fabric
    except ImportError:
        return None, None


def is_safe_to_submit(topology_name, host=None, port=None):
    """Check to see if a topology is currently running or is in the process of
    being killed. Assumes tunnel is already connected to Nimbus."""
    result = _list_topologies(run_kwargs={"hide": "both"},
                              host=host, port=port)

    if result.failed:
        raise RuntimeError("Error running streamparse.commands.list/-main")

    pattern = re.compile(r"{}\s+\|\s+(ACTIVE|KILLED)\s+\|"
                         .format(topology_name))
    if re.search(pattern, result.stdout):
        return False
    else:
        return True


@task
def prepare_topology():
    """Prepare a topology for running locally or deployment to a remote
    cluster.
    """
    if os.path.isdir("_resources/resources"):
        shutil.rmtree("_resources/resources")
    shutil.copytree("src", "_resources/resources")


def _list_topologies(host=None, port=None, run_args=None, run_kwargs=None):
    if run_args is None:
        run_args = []
    if run_kwargs is None:
        run_kwargs = {}
    run_kwargs['pty'] = True
    cmd = ["lein",
           "run -m streamparse.commands.list/-main"]
    if host:
        cmd.append("--host {}".format(host))
    if port:
        cmd.append("--port {}".format(port))
    return run(" ".join(cmd), *run_args, **run_kwargs)


@task
def list_topologies(env_name="prod"):
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    if is_ssh_for_nimbus(env_config):
        with ssh_tunnel(env_config["user"], host, 6627, port):
            return _list_topologies()
    return _list_topologies(host=host, port=port)


def _kill_topology(topology_name, wait=None,
                   host=None, port=None,
                   run_args=None, run_kwargs=None):
    if run_args is None:
        run_args = []
    if run_kwargs is None:
        run_kwargs = {}
    run_kwargs['pty'] = True
    wait_arg = ("--wait {wait}".format(wait=wait)) if wait is not None else ""
    cmd = ("lein run -m streamparse.commands.kill_topology/-main"
           " {topology_name} {wait}") \
        .format(
            topology_name=topology_name,
            wait=wait_arg
    )
    if host:
        cmd += " --host " + host
    if port:
        cmd += " --port " + str(port)
    return run(cmd, *run_args, **run_kwargs)


@task
def kill_topology(topology_name=None, env_name="prod", wait=None):
    topology_name, topology_file = get_topology_definition(topology_name)
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    if is_ssh_for_nimbus(env_config):
        with ssh_tunnel(env_config["user"], host, 6627, port):
            return _kill_topology(topology_name, wait)
    return _kill_topology(topology_name, wait, host=host, port=port)


@task
def jar_for_deploy():
    print("Cleaning from prior builds...")
    sys.stdout.flush()
    res = run("lein clean", hide="stdout")
    if not res.ok:
        raise RuntimeError("Unable to run 'lein clean'!\nSTDOUT:\n{}"
                           "\nSTDERR:\n{}".format(res.stdout, res.stderr))
    print("Creating topology uberjar...")
    sys.stdout.flush()
    res = run("lein uberjar", hide="stdout")
    if not res.ok:
        raise RuntimeError("Unable to run 'lein uberjar'!\nSTDOUT:\n{}"
                           "\nSTDERR:\n{}".format(res.stdout, res.stderr))
    # XXX: This will fail if more than one JAR is built
    lines = res.stdout.split()
    lines = [l.strip().lstrip("Created ") for l in lines
             if l.endswith("standalone.jar")]
    uberjar = lines[0]
    print("Uberjar created: {}".format(uberjar))
    sys.stdout.flush()
    return uberjar


@task(pre=["prepare_topology"])
def run_local_topology(name=None, time=0, workers=2, ackers=2, options=None,
                       debug=False):
    """Run a topology locally using Storm's LocalCluster class."""
    prepare_topology()

    name, topology_file = get_topology_definition(name)
    print("Running {} topology...".format(name))
    sys.stdout.flush()
    cmd = ["lein",
           "run -m streamparse.commands.run/-main",
           topology_file]
    cmd.append("-t {}".format(time))
    if debug:
        cmd.append("--debug")
    cmd.append("--option 'topology.workers={}'".format(workers))
    cmd.append("--option 'topology.acker.executors={}'".format(ackers))

    # Python logging settings
    if not os.path.isdir("logs"):
        os.makedirs("logs")
    log_path = os.path.join(os.getcwd(), "logs")
    print("Routing Python logging to {}.".format(log_path))
    sys.stdout.flush()
    cmd.append("--option 'streamparse.log.path=\"{}\"'"
               .format(log_path))
    cmd.append("--option 'streamparse.log.level=\"debug\"'")

    if options is None:
        options = []
    for option in options:
        cmd.append('--option {}'.format(option))
    full_cmd = " ".join(cmd)
    print("Running lein command to run local cluster:")
    print(full_cmd)
    sys.stdout.flush()
    run(full_cmd)


@task(pre=["prepare_topology"])
def submit_topology(name=None, env_name="prod", workers=2, ackers=2,
                    options=None, force=False, debug=False, wait=None):
    """Submit a topology to a remote Storm cluster."""
    prepare_topology()

    config = get_config()
    name, topology_file = get_topology_definition(name)
    env_name, env_config = get_env_config(env_name)
    host, port = get_nimbus_for_env_config(env_config)

    # Check if we need to maintain virtualenv during the process
    use_venv = env_config.get('use_virtualenv', True)
    if use_venv:
        activate_env(env_name)

    _pre_submit_hooks(name, env_name, env_config)

    if use_venv:
        config["virtualenv_specs"] = config["virtualenv_specs"].rstrip("/")
        create_or_update_virtualenvs(
            name, "{}/{}.txt".format(config["virtualenv_specs"], name)
        )

    # Prepare a JAR that doesn't have Storm dependencies packaged
    topology_jar = jar_for_deploy()

    print('Deploying "{}" topology...'.format(name))
    sys.stdout.flush()
    # Use ssh tunnel with Nimbus or use host/port for Thrift connection
    if is_ssh_for_nimbus(env_config):
        with ssh_tunnel(env_config["user"], host, 6627, port):
            print("ssh tunnel to Nimbus {}:{} established.".format(host, port))
            sys.stdout.flush()
            _kill_existing_topology(name, force, wait)
            _submit_topology(name, topology_file, topology_jar,
                             env_config, workers, ackers, options, debug)
            _post_submit_hooks(name, env_name, env_config)
    else:
        # This part doesn't use SSH tunnel at all
        _kill_existing_topology(name, force, wait, host=host, port=port)
        _submit_topology(name, topology_file, topology_jar,
                         env_config, workers, ackers, options, debug,
                         host=host, port=port)
        _post_submit_hooks(name, env_name, env_config)


def _kill_existing_topology(topology_name, force, wait, host=None, port=None):
    if force and not is_safe_to_submit(topology_name, host=host, port=port):
        print("Killing current \"{}\" topology.".format(topology_name))
        sys.stdout.flush()
        _kill_topology(topology_name, run_kwargs={"hide": "both"},
                       wait=wait, host=host, port=port)
        while not is_safe_to_submit(topology_name, host=host, port=port):
            print("Waiting for topology {} to quit...".format(topology_name))
            sys.stdout.flush()
            time.sleep(0.5)
        print("Killed.")
        sys.stdout.flush()


def _submit_topology(topology_name, topology_file, topology_jar,
                     env_config, workers, ackers, options=None, debug=False,
                     host=None, port=None):
    jvm_opts = [
        "-Dstorm.jar={}".format(topology_jar),
        "-Dstorm.options=",
        "-Dstorm.conf.file=",
    ]
    os.environ["JVM_OPTS"] = " ".join(jvm_opts)
    cmd = [
        "lein",
        "run -m streamparse.commands.submit_topology/-main",
        topology_file]

    if host:
        cmd.append("--host {}".format(host))
    if port:
        cmd.append("--port {}".format(port))
    if debug:
        cmd.append("--debug")

    cmd.append("--option 'topology.workers={}'".format(workers))
    cmd.append("--option 'topology.acker.executors={}'".format(ackers))

    if env_config.get('use_virtualenv', True):
        python_path = '/'.join([env_config["virtualenv_root"],
                                topology_name, "bin", "python"])

        cmd.append("--option 'topology.python.path=\"{}\"'".format(python_path))

    # Python logging settings
    log_config = env_config.get("log", {})
    log_path = log_config.get("path") or env_config.get("log_path")
    print("Routing Python logging to {}.".format(log_path))
    sys.stdout.flush()
    if log_path:
        cmd.append("--option 'streamparse.log.path=\"{}\"'"
                   .format(log_path))
    if isinstance(log_config.get("max_bytes"), int):
        cmd.append("--option 'streamparse.log.max_bytes={}'"
                   .format(log_config["max_bytes"]))
    if isinstance(log_config.get("backup_count"), int):
        cmd.append("--option 'streamparse.log.backup_count={}'"
                   .format(log_config["backup_count"]))
    if isinstance(log_config.get("level"), string_types):
        cmd.append("--option 'streamparse.log.level=\"{}\"'"
                   .format(log_config["level"].lower()))

    if options is None:
        options = []
    for option in options:
        # XXX: hacky Parse.ly-related workaround; must fix root
        # issue with -o options and string values
        if "deployment_stage" in option:
            key, val = option.split("=")
            cmd.append("--option '{}=\"{}\"'".format(key, val))
        else:
            cmd.append("--option {}".format(option))
    full_cmd = " ".join(cmd)
    print("Running lein command to submit topology to nimbus:")
    print(full_cmd)
    sys.stdout.flush()
    run(full_cmd)


def _pre_submit_hooks(topology_name, env_name, env_config):
    """Pre-submit hooks for invoke and fabric.
    """
    user_invoke, user_fabric = get_user_tasks()
    pre_submit_invoke = getattr(user_invoke, "pre_submit", None)
    if callable(pre_submit_invoke):
        pre_submit_invoke(topology_name, env_name, env_config)
    pre_submit_fabric = getattr(user_fabric, "pre_submit", None)
    if callable(pre_submit_fabric):
        pre_submit_fabric(topology_name, env_name, env_config)


def _post_submit_hooks(topology_name, env_name, env_config):
    """Post-submit hooks for invoke and fabric.
    """
    user_invoke, user_fabric = get_user_tasks()
    post_submit_invoke = getattr(user_invoke, "post_submit", None)
    if callable(post_submit_invoke):
        post_submit_invoke(topology_name, env_name, env_config)
    post_submit_fabric = getattr(user_fabric, "post_submit", None)
    if callable(post_submit_fabric):
        post_submit_fabric(topology_name, env_name, env_config)


@task
def tail_topology(topology_name=None, env_name=None, pattern=None):
    get_topology_definition(topology_name)
    activate_env(env_name)
    tail_logs(topology_name, pattern)


@task
def display_worker_uptime(env_name):
    topology_summary = '/api/v1/topology/summary'
    topology_detail = '/api/v1/topology/{topology}'
    component = '/api/v1/topology/{topology}/component/{component}'
    topo_summary_json = _get_ui_json(env_name, topology_summary)
    topology_ids = [x['id'] for x in topo_summary_json['topologies']]
    worker_stats = []

    for topology in topology_ids:
        topology_detail_json = _get_ui_json(env_name,
                                            topology_detail.format(topology=topology))
        spouts = [x['spoutId'] for x in topology_detail_json['spouts']]
        bolts = [x['boltId'] for x in topology_detail_json['bolts']]
        for comp in spouts + bolts:
            comp_detail = _get_ui_json(env_name,
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


@task
def display_stats(env_name, topology_name=None, component_name=None,
                  all_components=None):
    env_name = env_name
    if topology_name and all_components:
        _print_all_components(env_name, topology_name)
    elif topology_name and component_name:
        _print_component_status(env_name, topology_name, component_name)
    elif topology_name:
        _print_topology_status(env_name, topology_name)
    else:
        _print_cluster_status(env_name)


def _get_ui_jsons(env_name, api_paths):
    """Take env_name as a string and api_paths that should
    be a list of strings like '/api/v1/topology/summary'
    """
    _, env_config = get_env_config(env_name)
    host, _ = get_nimbus_for_env_config(env_config)
    # TODO: Get remote_ui_port from storm?
    remote_ui_port = 8080
    # SSH tunnel can take a while to close. Check multiples if necessary.
    local_ports = list(range(8081, 8090))
    shuffle(local_ports)
    for local_port in local_ports:
        try:
            data = {}
            with ssh_tunnel(env_config["user"],
                            host,
                            local_port=local_port,
                            remote_port=remote_ui_port):
                for api_path in api_paths:
                    r = requests.get('http://127.0.0.1:%s%s' % (local_port,
                                                                api_path))
                    data[api_path] = r.json()
            return data
        except Exception as e:
            if "already in use" in str(e):
                continue
            raise
    raise RuntimeError("Cannot find local port for SSH tunnel to Storm Head.")


def _get_ui_json(env_name, api_path):
    """Take env_name as a string and api_path that should
    be a string like '/api/v1/topology/summary'
    """
    return _get_ui_jsons(env_name, [api_path])[api_path]


def _print_cluster_status(env_name):
    jsons = _get_ui_jsons(env_name, ["/api/v1/cluster/summary",
                                     "/api/v1/topology/summary",
                                     "/api/v1/supervisor/summary"])
    # Print Cluster Summary
    ui_cluster_summary = jsons["/api/v1/cluster/summary"]
    columns = ['stormVersion', 'nimbusUptime', 'supervisors', 'slotsTotal',
               'slotsUsed', 'slotsFree', 'executorsTotal', 'tasksTotal']
    _print_stats_dict("Cluster summary",
                      ui_cluster_summary,
                      columns,
                      'r'
                      )
    # Print Topologies Summary
    ui_topologies_summary = jsons["/api/v1/topology/summary"]
    columns = ['name', 'id', 'status', 'uptime', 'workersTotal',
               'executorsTotal', 'tasksTotal']
    _print_stats_dict("Topology summary",
                      ui_topologies_summary['topologies'],
                      columns,
                      'r'
                      )
    # Print Supervisor Summary
    ui_supervisor_summary = jsons["/api/v1/supervisor/summary"]
    columns = ['id', 'host', 'uptime', 'slotsTotal', 'slotsUsed']
    _print_stats_dict("Supervisor summary",
                      ui_supervisor_summary['supervisors'],
                      columns,
                      'r',
                      {'host': 'l', 'uptime': 'l'}
                      )


def _get_topology_ui_detail(env_name, topology_name):
    env_name, env_config = get_env_config(env_name)
    host, _ = get_nimbus_for_env_config(env_config)
    topology_id = _get_topology_id(env_name, topology_name)
    detail_url = '/api/v1/topology/%s' % topology_id
    detail = _get_ui_json(env_name, detail_url)
    return detail


def _print_topology_status(env_name, topology_name):
    ui_detail = _get_topology_ui_detail(env_name, topology_name)
    # Print topology summary
    columns = ['name', 'id', 'status', 'uptime', 'workersTotal', 'executorsTotal', 'tasksTotal']
    _print_stats_dict("Topology summary",
                      ui_detail,
                      columns,
                      'r'
                      )
    # Print topology stats
    columns = ['windowPretty', 'emitted', 'transferred', 'completeLatency',
               'acked', 'failed']
    _print_stats_dict("Topology stats",
                      ui_detail['topologyStats'],
                      columns,
                      'r'
                      )
    # Print spouts
    if ui_detail.get('spouts'):
        columns = ['spoutId', 'emitted', 'transferred', 'completeLatency', 'acked', 'failed']
        _print_stats_dict("Spouts (All time)",
                          ui_detail['spouts'],
                          columns,
                          'r',
                          {'spoutId': 'l'}
                          )
    columns = ['boltId', 'executors', 'tasks', 'emitted', 'transferred', 'capacity',
               'executeLatency', 'executed', 'processLatency', 'acked', 'failed', 'lastError']
    _print_stats_dict("Bolt (All time)",
                      ui_detail['bolts'],
                      columns,
                      'r',
                      {'boltId': 'l'}
                      )


def _get_component_ui_detail(env_name, topology_name, component_names):
    if isinstance(component_names, basestring):
        component_names = [component_names]
    env_name, env_config = get_env_config(env_name)
    host, _ = get_nimbus_for_env_config(env_config)
    topology_id = _get_topology_id(env_name, topology_name)
    base_url = '/api/v1/topology/%s/component/%s'
    detail_urls = [base_url % (topology_id, name) for name in component_names]
    detail = _get_ui_jsons(env_name, detail_urls)
    if len(detail) == 1:
        return detail.values()[0]
    else:
        return detail


def _print_all_components(env_name, topology_name):
    topology_ui_detail = _get_topology_ui_detail(env_name, topology_name)
    spouts = map(lambda spout: spout['spoutId'], topology_ui_detail.get('spouts', {}))
    bolts = map(lambda spout: spout['boltId'], topology_ui_detail.get('bolts', {}))
    ui_details = _get_component_ui_detail(env_name, topology_name, chain(spouts, bolts))
    names_and_keys = zip(map(lambda ui_detail: ui_detail['name'], ui_details.values()),
                         ui_details.keys())
    for component_name, key in names_and_keys:
        _print_component_status(env_name, topology_name,
                                component_name, ui_details[key])


def _print_component_status(env_name, topology_name, component_name, ui_detail=None):
    if not ui_detail:
        ui_detail = _get_component_ui_detail(env_name, topology_name, component_name)
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
    columns = ['id', 'name', 'executors', 'tasks']
    _print_stats_dict("Component summary",
                      ui_detail,
                      columns,
                      'r'
                      )


def _print_bolt_stats(ui_detail):
    columns = ['windowPretty', 'emitted', 'transferred',
               'executeLatency', 'executed', 'processLatency',
               'acked', 'failed']
    _print_stats_dict("Bolt stats",
                      ui_detail['boltStats'],
                      columns,
                      'r',
                      {'windowPretty': 'l'}
                      )


def _print_input_stats(ui_detail):
    columns = ['component', 'stream', 'executeLatency', 'processLatency',
               'executed', 'acked', 'failed']
    if ui_detail['inputStats']:
        _print_stats_dict("Input stats (All time)",
                          ui_detail['inputStats'],
                          columns,
                          'r',
                          {'component': 'l'}
                          )


def _print_bolt_output_stats(ui_detail):
    if ui_detail['outputStats']:
        columns = ['stream', 'emitted', 'transferred']
        _print_stats_dict("Output stats (All time)",
                          ui_detail['outputStats'],
                          columns,
                          'r',
                          {'stream': 'l'}
                          )


def _print_spout_stats(ui_detail):
    columns = ['windowPretty', 'emitted', 'transferred', 'completeLatency',
               'acked', 'failed']
    data = ui_detail['spoutSummary'][-1].copy()
    _print_stats_dict("Spout stats",
                      data,
                      columns,
                      'r',
                      {'windowPretty': 'l'}
                      )


def _print_spout_output_stats(ui_detail):
    columns = ['stream', 'emitted', 'transferred', 'completeLatency',
               'acked', 'failed']
    _print_stats_dict("Output stats (All time)",
                      ui_detail['outputStats'],
                      columns,
                      'r',
                      {'stream': 'l'}
                      )


def _print_spout_executors(ui_detail):
    columns = ['id', 'uptime', 'host', 'port', 'emitted',
               'transferred', 'completeLatency', 'acked', 'failed']
    _print_stats_dict("Executors (All time)",
                      ui_detail['executorStats'],
                      columns,
                      'r',
                      {'host': 'l'}
                      )


def _print_stats_dict(header, data, columns, default_alignment, custom_alignment=None):
    print("# %s" % header)
    table = PrettyTable(columns)
    table.align = default_alignment
    if isinstance(data, list):
        for row in data:
            table.add_row([row.get(key, "MISSING") for key in columns])
    else:
        table.add_row([data.get(key, "MISSING") for key in columns])
    if custom_alignment:
        for column, alignment in iteritems(custom_alignment):
            table.align[column] = alignment
    print(table)


def _get_topology_id(env_name, topology_name):
    """Get toplogy ID from summary json provided by UI api
    """
    summary_url = '/api/v1/topology/summary'
    topology_summary = _get_ui_json(env_name, summary_url)
    for topology in topology_summary["topologies"]:
        if topology_name == topology["name"]:
            return topology["id"]


@task
def visualize_topology(name=None, flip=False):
    name, topology_file = get_topology_definition(name)
    print("Visualizing {} topology...".format(name))
    sys.stdout.flush()
    cmd = ["lein",
           "run -m streamparse.commands.visualize/-main",
           topology_file]
    if flip:
        cmd.append("-f")
    full_cmd = " ".join(cmd)
    print("Running lein command to visualize topology:")
    print(full_cmd)
    sys.stdout.flush()
    run(full_cmd)

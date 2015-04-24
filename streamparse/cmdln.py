from __future__ import absolute_import, print_function, unicode_literals

from docopt import docopt
from pkg_resources import parse_version

from .bootstrap import quickstart
from .ext.invoke import (list_topologies, kill_topology, run_local_topology,
                         submit_topology, tail_topology, visualize_topology,
                         display_stats, display_worker_uptime,
                         storm_lib_version)
from .version import __version__ as VERSION


# XXX: these are commands we're working on still
TODO_CMDS = """
        sparse debug [-e <env>]
        sparse restart [-e <env>]
        sparse attach [-e <env>]
        sparse logs [-e <env>]
"""


def main():
    """sparse: manage streamparse clusters.

    sparse provides a front-end to streamparse, a framework for creating Python
    projects for running, debugging, and submitting computation topologies
    against real-time streams, using Apache Storm.

    It requires the java and lein (Clojure build tool) to be on your $PATH, and
    uses lein and Clojure under the hood for JVM/Thrift interop.

    Usage:
        sparse quickstart <project_name>
        sparse run [-n <topology>] [-o <option>]... [-p <par>] [-w <workers>] [-a <ackers>] [-t <time>] [-dv]
        sparse submit [-n <topology>] [-o <option>]... [-p <par>] [-w <workers>] [-a <ackers>] [-e <env>] [-dvf] [--wait <seconds>]
        sparse list [-e <env>] [-v]
        sparse kill [-n <topology>] [-e <env>] [-v] [--wait <seconds>]
        sparse tail [-e <env>] [-n <topology>] [--pattern <regex>]
        sparse stats [-e <env>] [-n <topology>] [-c <component>|--all]
        sparse worker-uptime [-e <env>]
        sparse visualize [-n <topology>] [--flip]
        sparse (-h | --help)
        sparse --version

    Arguments:
        project_name                The name of your new streamparse project.

    Options:
        -h --help                   Show this screen.
        --version                   Show version.
        -v --verbose                Show verbose output for command.
        -e --environment <env>      The environment to use for the command
                                    corresponding to an environment in your
                                    "envs" dictionary in config.json. If you
                                    only have one environment specified,
                                    streamparse will automatically use this.
        -n --name <topology>        The name of the topology to deploy.  If you
                                    have only one topology defined in your
                                    topologies/ directory, streamparse
                                    will use it automatically.
        -c --component <component>  Topology component (bolt/spout) name as
                                    specified in Clojure topology specification
        -o --option <option>...     Topology option to use upon submit, e.g.
                                    "-o topology.debug=true" is equivalent to
                                    "--debug". May be repeated for multiple
                                    options.
                                    See "Topology Configuration" listing in
                                    Storm UI to confirm effects.
        -p --par <par>              Parallelism of topology; conveniently sets
                                    number of Storm workers and acker bolts
                                    at once to passed value [default: 2].
        -a --ackers <ackers>        Set number of acker bolts. Takes precedence
                                    over --par if both set.
        -w --workers <workers>      Set number of Storm workers. Takes
                                    precedence over --par if both set.
        -t --time <time>            Time (in seconds) to keep local cluster
                                    running.  If time <= 0, run indefinitely.
                                    [default: 0].
        --pattern <regex>           Apply pattern to files for "tail"
                                    subcommand.
        --flip                      Flip the visualization to be horizontal.
        --wait <seconds>            Seconds to wait before killing topology.
        -f --force                  Force a topology to submit by killing any
                                    currently running topologies of the same
                                    name.
        -d --debug                  Debug the given command.
    """
    args = docopt(main.__doc__, version="sparse " + VERSION)

    if args["run"]:
        time = int(args["--time"])
        ackers = workers = int(args["--par"])
        if args["--ackers"] is not None:
            ackers = int(args["--ackers"])
        if args["--workers"] is not None:
            workers = int(args["--workers"])
        options = args["--option"]
        run_local_topology(args["--name"], time, workers, ackers, options,
                           args["--debug"])
    elif args["list"]:
        list_topologies(args["--environment"])
    elif args["kill"]:
        kill_topology(args["--name"], args["--environment"], args["--wait"])
    elif args["quickstart"]:
        quickstart(args['<project_name>'])
    elif args["submit"]:
        ackers = workers = int(args["--par"])
        if args["--ackers"] is not None:
            ackers = int(args["--ackers"])
        if args["--workers"] is not None:
            workers = int(args["--workers"])
        options = args["--option"]
        submit_topology(name=args["--name"], env_name=args["--environment"],
                        workers=workers, ackers=ackers, options=options,
                        force=args["--force"], debug=args["--debug"],
                        wait=args["--wait"])
    elif args["tail"]:
        tail_topology(args["--name"], args["--environment"], args["--pattern"])
    elif args["stats"] or args["worker-uptime"]:
        storm_version = storm_lib_version()
        if storm_version >= parse_version('0.9.2-incubating'):
            if args["stats"]:
                display_stats(args["--environment"], args.get("--name"),
                              args.get("--component"), args.get("--all"))
            else:
                display_worker_uptime(args["--environment"])
        else:
            print("ERROR: Storm {} does not support this command."
                  .format(storm_version))
    elif args["visualize"]:
        visualize_topology(args["--name"])


if __name__ == "__main__":
    main()

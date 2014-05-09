from docopt import docopt
from invoke import run

from ext.fabric import *
from ext.invoke import *
from bootstrap import quickstart


# XXX: these are commands we're working on still
TODO_CMDS = """
        sparse setup [-e <env>]
        sparse debug [-e <env>]
        sparse kill [-e <env>]
        sparse restart [-e <env>]
        sparse attach [-e <env>]
        sparse logs [-e <env>]

"""


def main():
    """sparse: manage streamparse clusters.

    sparse provides a front-end to streamparse, a framework for creating Python
    projects for running, debugging, and submitting computation topologies against
    real-time streams, using Apache Storm.

    It requires the lein (Clojure build tool) to be on your $PATH, and uses
    lein and Clojure under the hood for JVM interop.

    Usage:
        sparse quickstart <project_dir>
        sparse deploy [-n <topology_name>] [-e <env>]
        sparse list
        sparse kill <topology_name>
        sparse run [-n <topology_name>] [-e <env>] [-t <time>] [--debug]
        sparse (-h | --help)
        sparse --version

    Options:
        -h --help           Show this screen.
        --version           Show version.
        -e <env>            Set environment; as described in config.json [default: local].
        -n <topology_name>  The name of the topology.
        -t <time>           Time (in seconds) to keep cluster running [default: 5].
        --verbose           Verbose output.
        --debug             Debug output.
    """
    args = docopt(main.__doc__, version="sparse 0.1")
    if args["run"]:
        time = int(args["-t"])
        run_local_topology(args["-n"], time, args["--debug"])
    elif args["list"]:
        list_topologies()
    elif args["quickstart"]:
        quickstart(args['<project_dir>'])
    elif args["deploy"]:
        deploy_topology(args["-n"])


if __name__ == "__main__":
    main()

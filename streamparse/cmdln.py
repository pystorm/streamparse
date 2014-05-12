from docopt import docopt

from ext.fabric import *
from ext.invoke import *
from bootstrap import quickstart


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
        sparse run [-n <topology>] [-t <time>] [-dv]
        sparse submit [-e <env>] [-n <topology>] [-dv]
        sparse list [-e <env>] [-v]
        sparse kill [-n <topology>] [-e <env>] [-v]
        sparse tail [-e <env>]
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
        -t --time <time>            Time (in seconds) to keep local cluster
                                    running [default: 5].
        -d --debug                  Debug the given command.
    """
    args = docopt(main.__doc__, version="sparse 0.1")

    if args["run"]:
        time = int(args["--time"])
        run_local_topology(args["--name"], time, args["--debug"])
    elif args["list"]:
        list_topologies(args["--environment"])
    elif args["kill"]:
        kill_topology(args["--name"], args["--environment"])
    elif args["quickstart"]:
        quickstart(args['<project_name>'])
    elif args["submit"]:
        submit_topology(args["--name"], args["--environment"])
    elif args["tail"]:
        tail_topology(args["--environment"])


if __name__ == "__main__":
    main()

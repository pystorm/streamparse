from docopt import docopt
from invoke import run

import json

from os import path

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
        sparse run [-e <env>] [-t <time>] [--debug]
        sparse deploy [-e <env>]
        sparse list
        sparse (-h | --help)
        sparse --version

    Options:
        -h --help         Show this screen.
        --version         Show version.
        -e <env>          Set environment; as described in config.json [default: local].
        -t <time>         Time (in milliseconds) to keep cluster running [default: 10000].
        --verbose         Verbose output.
        --debug           Debug output.
    """
    args = docopt(main.__doc__, version="sparse 0.1")
    if args["run"]:
        cfg = json.load(open("config.json"))
        topo_dir = cfg["topology_specs"]
        topo_first = cfg["topologies"][0]
        print "Running {topo_name} topology...".format(topo_name=topo_first)
        time = args["-t"]
        debug = args["--debug"]
        topology = path.join(topo_dir, topo_first) + ".clj"
        cmd = "invoke stormlocal --topology={topology} --time={time}".format(
            topology=topology, time=time, debug=debug)
        if debug:
            cmd += " --debug"
        run(cmd)
    elif args["list"]:
        print "invoke (local) tasks:"
        run("invoke -l")
        print
        print "fabric (remote) tasks:"
        run("fab -l")
    elif args["quickstart"]:
        quickstart(args['<project_dir>'])


if __name__ == "__main__":
    main()

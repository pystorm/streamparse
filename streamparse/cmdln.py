from docopt import docopt
from invoke import run

def main():
    """sparse: manage StreamParse clusters.

    sparse provides a front-end to StreamParse, a framework for creating Python
    projects for running, debugging, and submitting Storm topologies for data
    processing.

    It requires the lein (Clojure build tool) to be on your $PATH, and uses
    lein and Clojure under the hood for JVM interop.

    Usage:
        sparse quickstart <proj_name>
        sparse setup [-e ENV]
        sparse run [-e ENV]
        sparse debug [-e ENV]
        sparse kill [-e ENV]
        sparse restart [-e ENV]
        sparse attach [-e ENV]
        sparse list [-e ENV]
        sparse submit [-e ENV]
        sparse logs [-e ENV]
        sparse (-h | --help)
        sparse --version

    Options:
        -h --help         Show this screen.
        --version         Show version.
        -e ENV            Set environment [default: local].
        --verbose         Verbose output.
        --debug           Debug output.
    """
    args = docopt(main.__doc__, version="sparse 0.1")
    print args
    if args["run"]:
        print "Running wordcount topology..."
        run("lein run -s topologies/wordcount.clj")
    elif args["debug"]:
        print "Debugging wordcount topology..."
        run("lein run -s topologies/wordcount.clj")
    elif args["list"]:
        print "invoke tasks:"
        run("invoke -l")
        print
        print "fabric tasks:"
        run("fab -l")
    elif args["setup"]:
        print "Setting up virtualenv on remote cluster..."
        run("fab workers setup_virtualenv")
    elif args["quickstart"]:
        print "Starting a new sparse project..."
        run("echo mkdir -p yourproj ...")


if __name__ == "__main__":
    main()

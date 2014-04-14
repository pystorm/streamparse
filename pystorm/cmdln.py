from docopt import docopt


def main():
    """stormpy

    Usage:
        stormpy run-local
        stormpy debug-local

    Options:
        -h --help           Show this screen.
        --version           Show version.
        --debug             Debug output.
    """
    args = docopt(main.__doc__, version="stormpy 0.1")
    if args["run-local"]:
        print "run local"
    elif args["debug-local"]:
        print "debug local"


if __name__ == "__main__":
    main()

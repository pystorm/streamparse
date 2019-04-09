"""
Create new streamparse project template.
"""

from streamparse.bootstrap import quickstart


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser(
        "quickstart", description=__doc__, help=main.__doc__
    )
    subparser.set_defaults(func=main)
    subparser.add_argument("project_name", help="Name of new streamparse project.")


def main(args):
    """ Create new streamparse project template. """
    quickstart(args.project_name)

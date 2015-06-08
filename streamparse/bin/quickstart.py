from __future__ import absolute_import
from streamparse.bootstrap import quickstart


def subparser_hook(subparsers):
    quickstart_subparser = subparsers.add_parser('quickstart')
    quickstart_subparser.set_defaults(func=main)
    quickstart_subparser.add_argument(
        'project_name',
        help = 'Name of new streamparse project.'
    )

def main(args):
    quickstart(args.project_name)


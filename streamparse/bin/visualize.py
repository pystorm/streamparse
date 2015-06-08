from __future__ import absolute_import
from streamparse.ext.invoke import visualize_topology


def subparser_hook(subparsers):
    visualize_subparser = subparsers.add_parser('visualize')
    visualize_subparser.set_defaults(func=main)
    visualize_subparser.add_argument(
        '-f', '--flip',
        dest   = 'flip',
        action = 'store_true',
        help   = 'Flip the visualization to be horizontal.'
    )
    visualize_subparser.add_argument(
        '-n', '--name',
        dest = 'name', help = (
            'The name of the topology to visualize. If you have only one '
            'topology defined in your topologies/ directory, streamparse '
            'will use it automatically.'
        )
    )


def main(args):
    visualize_topology(args.name)

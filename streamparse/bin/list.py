from __future__ import absolute_import
from streamparse.ext.invoke import list_topologies


def subparser_hook(subparsers):
    list_subparser = subparsers.add_parser('list')
    list_subparser.set_defaults(func=main)
    list_subparser.add_argument(
        '-e', '--envirionment',
        dest = 'environ',
        help = (
            'The environment to use for the command corresponding to an'
            'environment in your "envs" dictionary in config.json. If you'
            'only have one environment specified, streamparse will'
            'automatically use this.'
       )
    )
    list_subparser.add_argument(
        '-v', '--verbose',
        dest   = 'verbose',
        action = 'store_true',
        help   = 'Show verbose output for command.'
    )

def main(args):
    list_topologies(args.environ)


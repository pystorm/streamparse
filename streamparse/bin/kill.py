from __future__ import absolute_import
from streamparse.ext.invoke import kill_topology


def subparser_hook(subparsers):
    kill_subparser = subparsers.add_parser('kill')
    kill_subparser.set_defaults(func=main)
    kill_subparser.add_argument(
        '-n', '--name',
        dest = 'name',
        help = (
            'The name of the topology to kill. If you have only one topology'
            'defined in your topologies/ directory, streamparse will use it'
            'automatically.'
        )
    )
    kill_subparser.add_argument(
        '-e', '--envirionment',
        dest = 'environ',
        help = (
            'The environment to use for the command corresponding to an'
            'environment in your "envs" dictionary in config.json. If you'
            'only have one environment specified, streamparse will'
            'automatically use this.'
       )
    )
    kill_subparser.add_argument(
        '-v', '--verbose',
        dest   = 'verbose',
        action = 'store_true',
        help   = 'Show verbose output for command.'
    )
    kill_subparser.add_argument(
        '-wait',
        dest    = 'wait',
        type    = int,
        default = 5,
        help    = 'Seconds to wait before killing topology.'
    )

def main(args):
    kill_topology(args.name, args.environ, args.wait)


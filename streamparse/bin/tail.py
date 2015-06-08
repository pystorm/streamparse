from __future__ import absolute_import
from streamparse.ext.invoke import tail_topology


def subparser_hook(subparsers):
    tail_subparser = subparsers.add_parser('tail')
    tail_subparser.set_defaults(func=main)
    tail_subparser.add_argument(
        '-e', '--envirionment',
        dest = 'environ',
        help = (
            'The environment to use for the command corresponding to an'
            'environment in your "envs" dictionary in config.json. If you'
            'only have one environment specified, streamparse will'
            'automatically use this.'
       )
    )
    tail_subparser.add_argument(
        '-n', '--name',
        dest = 'name', help = ( 'The name of the topology to run. If you have only one topology'
            'defined in your topologies/ directory, streamparse will use it'
            'automatically.'
        )
    )
    tail_subparser.add_argument(
        '--pattern',
        dest    = 'pattern',
        help    = 'Apply pattern to files for "tail" subcommand.',
    )


def main(args):
    tail_topology(args.name, args.environ, args.pattern)


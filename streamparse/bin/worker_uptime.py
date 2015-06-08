from __future__ import absolute_import
from streamparse.ext.invoke import display_worker_uptime


def subparser_hook(subparsers):
    worker_up_subparser = subparsers.add_parser('worker_uptime')
    worker_up_subparser.set_defaults(func=main)
    worker_up_subparser.add_argument(
        '-e', '--envirionment',
        dest = 'environ',
        help = (
            'The environment to use for the command corresponding to an'
            'environment in your "envs" dictionary in config.json. If you'
            'only have one environment specified, streamparse will'
            'automatically use this.'
       )
    )

def main(args):
    display_worker_uptime(args.environ)

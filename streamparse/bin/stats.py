from __future__ import absolute_import, print_function
from pkg_resources import parse_version
from streamparse.ext.invoke import (
    storm_lib_version,
    display_stats,
    display_worker_uptime
)


def subparser_hook(subparsers):
    stats_subparser = subparsers.add_parser('stats')
    stats_subparser.set_defaults(func=main)
    stats_subparser.add_argument(
        '--all',
        dest   = 'all',
        action = 'store_true',
        help   = 'All available stats.'
    )
    stats_subparser.add_argument(
        '-c', '--components',
        dest = 'name',
        help = (
            'Topology component (bolt/spout) name asspecified in Clojure '
            'topology specification'
        )
    )
    stats_subparser.add_argument(
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
    storm_version = storm_lib_version()
    if storm_version >= parse_version('0.9.2-incubating'):
        display_stats(args.environment, args.name, args.component, args.all)
    else:
        print("ERROR: Storm {0} does not support this command.".format(
            storm_version)
        )

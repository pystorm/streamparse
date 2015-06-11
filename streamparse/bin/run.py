from __future__ import absolute_import
from streamparse.ext.invoke import run_local_topology

def subparser_hook(subparsers):
    run_subparser = subparsers.add_parser('run')
    run_subparser.set_defaults(func=main)
    run_subparser.add_argument(
        '-a', '--ackers',
        dest = 'ackers',
        help = (
            'Set number of acker bolts. Takes precedence over --par if both'
            'set.'
       ))
    run_subparser.add_argument(
        '-d', '--debug',
        dest   = 'debug',
        action = 'store_true',
        help   = 'Debug the given command.'
    )
    run_subparser.add_argument(
        '-e', '--envirionment',
        dest = 'environ',
        help = (
            'The environment to use for the command corresponding to an'
            'environment in your "envs" dictionary in config.json. If you'
            'only have one environment specified, streamparse will'
            'automatically use this.'
       )
    )
    run_subparser.add_argument(
        '-n', '--name',
        dest = 'name', help = (
            'The name of the topology to run. If you have only one topology'
            'defined in your topologies/ directory, streamparse will use it'
            'automatically.'
        )
    )
    run_subparser.add_argument(
        '-o', '--option',
        dest   = 'options',
        action = 'append',
        help   = (
            'Topology option to use upon submit, e.g. "-o topology.dbug=true" '
            'is equivalent to "--debug". May be repeated multiple for multiple'
            'options.'
        )
    )
    run_subparser.add_argument(
        '-p', '--par',
        dest    = 'par',
        default = 2,
        type    = int,
        help    = (
            'Parallelism of topology; conveniently sets number of Storm'
            'workers and acker bolts at once to passed value [default: 2].'
        )
    )
    run_subparser.add_argument(
        '-t', '--time',
        dest    = 'time',
        default = 0,
        type    = int,
        help    = (
            'Time (in seconds) to keep local cluster running. If time <= 0,'
            'run indefinitely. [default: 0].'
        )
    )
    run_subparser.add_argument(
        '-v', '--verbose',
        dest   = 'verbose',
        action = 'store_true',
        help   = 'Show verbose output for command.'
    )
    run_subparser.add_argument(
        '--wait',
        dest    = 'wait',
        type    = int,
        default = 5,
        help    = 'Seconds to wait before killing topology.'
    )
    run_subparser.add_argument(
        '-w', '--workers',
        dest   = 'workers',
        type   = int,
        help   = (
            'Set number of Storm workers. Takes precedence over --par if both'
            ' set.'
        )
    )

def main(args):
    run_local_topology(args.name, args.time, args.workers, args.ackers, args.options, args.debug)

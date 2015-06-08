from __future__ import absolute_import
from streamparse.ext.invoke import submit_topology

def subparser_hook(subparsers):
    submit_subparser = subparsers.add_parser('submit')
    submit_subparser.set_defaults(func=main)
    submit_subparser.add_argument(
        '-a', '--ackers',
        dest = 'ackers',
        help = (
            'Set number of acker bolts. Takes precedence over --par if both'
            'set.'
       )
    )
    submit_subparser.add_argument(
        '-d', '--debug',
        dest   = 'debug',
        action = 'store_true',
        help   = 'Debug the given command.'
    )
    submit_subparser.add_argument(
        '-e', '--envirionment',
        dest = 'environ',
        help = (
            'The environment to use for the command corresponding to an'
            'environment in your "envs" dictionary in config.json. If you'
            'only have one environment specified, streamparse will'
            'automatically use this.'
       )
    )
    submit_subparser.add_argument(
        '-f', '--force',
        dest   = 'force',
        action = 'store_true',
        help   = (
            'Force a topology to submit by killing any currently running '
            'topologies of the same name.'
        )
    )
    submit_subparser.add_argument(
        '-n', '--name',
        dest = 'name', help = ( 'The name of the topology to run. If you have only one topology'
            'defined in your topologies/ directory, streamparse will use it'
            'automatically.'
        )
    )
    submit_subparser.add_argument(
        '-o', '--option',
        dest   = 'options',
        action = 'append',
        help   = (
            'Topology option to use upon submit, e.g. "-o topology.dbug=true" '
            'is equivalent to "--debug". May be repeated multiple for multiple'
            'options.'
        )
    )
    submit_subparser.add_argument(
        '-p', '--par',
        dest    = 'par',
        default = 2,
        type    = int,
        help    = (
            'Parallelism of topology; conveniently sets number of Storm'
            'workers and acker bolts at once to passed value [default: 2].'
        )
    )
    submit_subparser.add_argument(
        '-t', '--time',
        dest    = 'time',
        default = 0,
        type    = int,
        help    = (
            'Time (in seconds) to keep local cluster running. If time <= 0,'
            'run indefinitely. [default: 0].'
        )
    )
    submit_subparser.add_argument(
        '-v', '--verbose',
        dest   = 'verbose',
        action = 'store_true',
        help   = 'Show verbose output for command.'
    )
    submit_subparser.add_argument(
        '--wait',
        dest    = 'wait',
        type    = int,
        default = 5,
        help    = 'Seconds to wait before killing topology.'
    )
    submit_subparser.add_argument(
        '-w', '--workers',
        dest   = 'workers',
        type   = int,
        help   = (
            'Set number of Storm workers. Takes precedence over --par if both'
            ' set.'
        )
    )


def main(args):
    submit_topology(
        name     = args.name,
        env_name = args.environment,
        workers  = args.workers,
        ackers   = args.ackers,
        options  = args.options,
        force    = args.force,
        debug    = args.debug,
        wait     = args.wait
    )

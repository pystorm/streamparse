"""
Functions for adding common CLI arguments to argparse sub-commands.
"""
import argparse
import copy


class _StoreDictAction(argparse.Action):
    """Action for storing key=val option strings as a single dict."""
    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        if nargs == 0:
            raise ValueError('nargs for store_dict actions must be > 0')
        if const is not None and nargs != '?':
            raise ValueError('nargs must be "?" to supply const')
        super(_StoreDictAction, self).__init__(option_strings=option_strings,
                                               dest=dest,
                                               nargs=nargs,
                                               const=const,
                                               default=default,
                                               type=type,
                                               choices=choices,
                                               required=required,
                                               help=help,
                                               metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is None:
            setattr(namespace, self.dest, {})
        # Only doing a copy here because that's what _AppendAction does
        items = copy.copy(getattr(namespace, self.dest))
        key, val = values.split("=", 1)
        try:
            val = int(val)
        except ValueError:
            try:
                val = float(val)
            except ValueError:
                pass
        items[key] = val
        setattr(namespace, self.dest, items)


def add_ackers(parser):
    """ Add --ackers option to parser """
    parser.add_argument('-a', '--ackers',
                        help='Set number of acker bolts. Takes precedence over '
                             '--par if both set.',
                        type=int)


def add_debug(parser):
    """ Add --debug option to parser """
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Set topology.debug and produce debugging output.')


def add_environment(parser):
    """ Add --environment option to parser """
    parser.add_argument('-e', '--environment',
                        help='The environment to use for the command.  '
                             'Corresponds to an environment in your '
                             '"envs" dictionary in config.json.  If you '
                             'only have one environment specified, '
                             'streamparse will automatically use this.')


def add_name(parser):
    """ Add --name option to parser """
    parser.add_argument('-n', '--name',
                        help='The name of the topology to act on.  If you have '
                             'only one topology defined in your "topologies" '
                             'directory, streamparse will use it '
                             'automatically.')


def add_options(parser):
    """ Add --option options to parser """
    parser.add_argument('-o', '--option',
                        dest='options',
                        action=_StoreDictAction,
                        help='Topology option to pass on to Storm. For example,'
                             ' "-o topology.debug=true" is equivalent to '
                             '"--debug".  May be repeated multiple for multiple'
                             ' options.')


def add_par(parser):
    """ Add --par option to parser """
    parser.add_argument('-p', '--par',
                        default=2,
                        type=int,
                        help='Parallelism of topology; conveniently sets '
                             'number of Storm workers and acker bolts at once '
                             'to passed value. (default: %(default)s)')

def add_pattern(parser):
    """ Add --pattern option to parser """
    parser.add_argument('--pattern',
                        help='Pattern of log files to operate on.')


def add_simple_jar(parser):
    """ Add --simple_jar option to parser. """
    parser.add_argument("-s", "--simple_jar",
                        action='store_true',
                        help='Instead of creating an Uber-JAR for the '
                             'topology, which contains all of its JVM '
                             'dependencies, create a simple JAR with just the '
                             'code for the project.  This is useful when your '
                             'project is pure Python and has no JVM '
                             'dependencies.')


def add_wait(parser):
    """ Add --wait option to parser """
    parser.add_argument('--wait',
                        type=int,
                        default=5,
                        help='Seconds to wait before killing topology. '
                             '(default: %(default)s)')


def add_workers(parser):
    """ Add --workers option to parser """
    parser.add_argument('-w', '--workers',
                        type=int,
                        help='Set number of Storm workers. Takes precedence '
                             'over --par if both set.')


def resolve_ackers_workers(args):
    """ Set --ackers and --workers to --par if they're None. """
    if args.ackers is None:
        args.ackers = args.par
    if args.workers is None:
        args.workers = args.par

"""
Run a local Storm topology.
"""

from __future__ import absolute_import, print_function

from tempfile import NamedTemporaryFile

import yaml
from fabric.api import local

from ..util import (get_topology_definition, get_topology_from_file,
                    local_storm_version, storm_lib_version)
from .common import (add_ackers, add_debug, add_environment, add_name,
                     add_options, add_par, add_workers, resolve_ackers_workers)
from .jar import jar_for_deploy


def run_local_topology(name=None, time=0, workers=2, ackers=2, options=None,
                       debug=False):
    """Run a topology locally using Flux and `storm jar`."""
    storm_options = {'topology.workers': workers,
                     'topology.acker.executors': ackers,
                     'topology.debug': debug}
    if debug:
        storm_options['pystorm.log.level'] = 'debug'
    name, topology_file = get_topology_definition(name)
    topology_class = get_topology_from_file(topology_file)

    # Check Storm version is the same
    local_version = local_storm_version()
    project_version = storm_lib_version()
    if local_version != project_version:
        raise ValueError('Local Storm version, {}, is not the same as the '
                         'version in your project.clj, {}. The versions must '
                         'match.'.format(local_version, project_version))

    # Prepare a JAR that has Storm dependencies packaged
    topology_jar = jar_for_deploy(simple_jar=False)

    if options is not None:
        storm_options.update(options)

    if time <= 0:
        time = 9223372036854775807  # Max long value in Java

    # Write YAML file
    with NamedTemporaryFile(suffix='.yaml', delete=False) as yaml_file:
        topology_flux_dict = topology_class.to_flux_dict(name)
        topology_flux_dict['config'] = storm_options
        yaml.safe_dump(topology_flux_dict, yaml_file)
        cmd = ('storm jar {jar} org.apache.storm.flux.Flux --local --no-splash '
               '--sleep {time} {yaml}'.format(jar=topology_jar,
                                              time=time,
                                              yaml=yaml_file.name))
        local(cmd)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('run',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_ackers(subparser)
    add_debug(subparser)
    add_environment(subparser)
    add_name(subparser)
    add_options(subparser)
    add_par(subparser)
    subparser.add_argument('-t', '--time',
                           default=0,
                           type=int,
                           help='Time (in seconds) to keep local cluster '
                                'running. If time <= 0, run indefinitely. '
                                '(default: %(default)s)')
    add_workers(subparser)


def main(args):
    """ Run the local topology with the given arguments """
    resolve_ackers_workers(args)
    run_local_topology(name=args.name, time=args.time, workers=args.workers,
                       ackers=args.ackers, options=args.options,
                       debug=args.debug)

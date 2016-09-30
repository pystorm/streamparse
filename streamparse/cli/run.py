"""
Run a local Storm topology.

Note: If you have "org.apache.storm" in your uberjar-exclusions list in your
project.clj, this will fail. Temporarily remove it to use `sparse run`. You will
also need to add [org.apache.storm/flux-core "1.0.1"] to dependencies.
"""

from __future__ import absolute_import, print_function

from argparse import RawDescriptionHelpFormatter
from tempfile import NamedTemporaryFile

from fabric.api import local
from ruamel import yaml

from ..util import (get_env_config, get_topology_definition,
                    get_topology_from_file, local_storm_version,
                    storm_lib_version)
from .common import (add_ackers, add_debug, add_environment, add_name,
                     add_options, add_workers, resolve_options)
from .jar import jar_for_deploy


def run_local_topology(name=None, env_name=None, time=0, options=None):
    """Run a topology locally using Flux and `storm jar`."""
    name, topology_file = get_topology_definition(name)
    env_name, env_config = get_env_config(env_name)
    topology_class = get_topology_from_file(topology_file)

    storm_options = resolve_options(options, env_config, topology_class, name)
    if storm_options['topology.acker.executors'] != 0:
        storm_options['topology.acker.executors'] = 1
    storm_options['topology.workers'] = 1

    # Check Storm version is the same
    local_version = local_storm_version()
    project_version = storm_lib_version()
    if local_version != project_version:
        raise ValueError('Local Storm version, {}, is not the same as the '
                         'version in your project.clj, {}. The versions must '
                         'match.'.format(local_version, project_version))

    # Prepare a JAR that has Storm dependencies packaged
    topology_jar = jar_for_deploy(simple_jar=False)

    if time <= 0:
        time = 9223372036854775807  # Max long value in Java

    # Write YAML file
    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as yaml_file:
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
                                      help=main.__doc__,
                                      formatter_class=RawDescriptionHelpFormatter)
    subparser.set_defaults(func=main)
    add_ackers(subparser)
    add_debug(subparser)
    add_environment(subparser)
    add_name(subparser)
    add_options(subparser)
    subparser.add_argument('-t', '--time',
                           default=0,
                           type=int,
                           help='Time (in seconds) to keep local cluster '
                                'running. If time <= 0, run indefinitely. '
                                '(default: %(default)s)')
    add_workers(subparser)


def main(args):
    """Run the local topology with the given arguments"""
    run_local_topology(name=args.name, time=args.time, options=args.options,
                       env_name=args.environment)

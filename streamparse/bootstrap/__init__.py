"""Utilities for bootstrapping streamparse projects."""
from contextlib import contextmanager
import os
import sys

from fabric.colors import green, red, blue
from invoke import run
from jinja2 import Environment, FileSystemLoader


_path_prefixes = []
_path_prefix = ''
_root = os.path.abspath(os.path.dirname(__file__))
_here = lambda *x: os.path.join(_root, *x)
_env = Environment(loader=FileSystemLoader(_here('project')))

@contextmanager
def _cd(path):
    global _path_prefixes
    global _path_prefix
    _path_prefixes.append(path)
    _path_prefix = '/'.join(_path_prefixes)
    yield
    _path_prefixes.pop()
    _path_prefix = '/'.join(_path_prefixes)


def _mkdir(path):
    path = '{}/{}'.format(_path_prefix, path) if _path_prefix != '' else path
    print '\t{:<20} {}'.format(green('create'), path)
    run('mkdir -p {}'.format(path))


def _cp(src, dest):
    dest = '{}/{}'.format(_path_prefix, dest) if _path_prefix != '' else dest
    print '\t{:<20} {}'.format(green('create'), dest)
    run('cp {} {}'.format(src, dest))


def _touch(filename):
    filename = '{}/{}'.format(_path_prefix, filename) if _path_prefix != '' \
               else filename
    print '\t{:<20} {}'.format(green('create'), filename)
    run('touch {}'.format(filename))


def _generate(template_filename, dest):
    dest = '{}/{}'.format(_path_prefix, dest) if _path_prefix != '' \
           else dest
    print '\t{:<20} {}'.format(green('create'), dest)
    template = _env.get_template(template_filename)
    context = {}  # TODO: should be jinja2 context stuff
    with open(dest, 'w') as fp:
        fp.write(template.render(**context))


def quickstart(project_name):
    # TODO: alternate way maybe to do all of this is do something like
    # glob.glob('project/**/*') and then we copy everything that's doesn't have
    # jinja2 in filename, generate the jinja2 stuff
    if os.path.exists(project_name):
        print '{}: folder "{}" already exists'.format(red('error'), project_name)
        sys.exit(1)

    print 'Creating your {} sparse project...'\
          .format(blue(project_name))

    _mkdir(project_name)
    with _cd(project_name):
        _generate('config.jinja2.json', 'config.json')
        _touch('fabfile.py')
        _generate('project.jinja2.clj', 'project.clj')
        _touch('README.md')
        _mkdir('src')
        with _cd('src'):
            _cp(_here('project', 'src', 'wordcount.py'), 'wordcount.py')
            _cp(_here('project', 'src', 'wordlib.py'), 'wordlib.py')
        _cp(_here('project', 'tasks.py'), 'tasks.py')
        _mkdir('topologies')
        with _cd('topologies'):
            _cp(_here('project', 'topologies', 'wordcount.clj'), 'wordcount.clj')
        _mkdir('virtualenvs')
        with _cd('virtualenvs'):
            _cp(_here('project', 'virtualenvs', 'wordcount.txt'),
                'wordcount.txt')


# * src/
#     * wordlib.py: example support library in Python
#     * wordcount.py: example Spout & Bolt implementation in Python
# * topologies/
#     * wordcount.clj: ``clj`` file with topology configuration in Clojure DSL
# * virtualenvs/
#     * wordcount.txt: ``requirements`` file to express Python dependencies
# * config.json: config file w/ Storm cluster hostnames and code locations
# * project.clj: ``lein`` project file to express Storm dependencies
# * fabfile.py: remote management tasks (fabric, customizable)
# * tasks.py: local management tasks (invoke, customizable)

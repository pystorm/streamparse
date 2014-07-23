"""
Utilities for bootstrapping streamparse projects.
"""
from __future__ import absolute_import, print_function, unicode_literals

from contextlib import contextmanager
import os
import sys
import shutil

from fabric.colors import green, red, blue
from jinja2 import Environment, FileSystemLoader

import pkg_resources

_path_prefixes = []
_path_prefix = ''
_root = os.path.abspath(os.path.dirname(__file__))


def _here(*paths):
    path = os.path.join(*paths)
    filename = pkg_resources.resource_filename(__name__, path)
    return filename

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
    print('    {:<18} {}'.format(green('create'), path))
    os.makedirs(path)


def _cp(src, dest):
    dest = '{}/{}'.format(_path_prefix, dest) if _path_prefix != '' else dest
    print('    {:<18} {}'.format(green('create'), dest))
    shutil.copy(src, dest)


def _touch(filename):
    filename = '{}/{}'.format(_path_prefix, filename) if _path_prefix != '' \
               else filename
    print('    {:<18} {}'.format(green('create'), filename))
    with open(filename, 'w'):
        pass


def _generate(template_filename, dest):
    dest = '{}/{}'.format(_path_prefix, dest) if _path_prefix != '' \
           else dest
    print('    {:<18} {}'.format(green('create'), dest))
    template = _env.get_template(template_filename)
    with open(dest, 'w') as fp:
        fp.write(template.render())


def quickstart(project_name):
    # TODO: alternate way maybe to do all of this is do something like
    # glob.glob('project/**/*') and then we copy everything that's doesn't have
    # jinja2 in filename, generate the jinja2 stuff
    if os.path.exists(project_name):
        print('{}: folder "{}" already exists'.format(red('error'),
                                                      project_name))
        sys.exit(1)

    print('\nCreating your %s streamparse project...' % (blue(project_name)))
    _env.globals['project_name'] = project_name

    _mkdir(project_name)
    with _cd(project_name):
        _cp(_here('project', 'gitignore'), '.gitignore')
        _generate('config.jinja2.json', 'config.json')
        _cp(_here('project', 'fabfile.py'), 'fabfile.py')
        _generate('project.jinja2.clj', 'project.clj')
        _touch('README.md')
        _mkdir('src')
        with _cd('src'):
            _mkdir('bolts')
            with _cd('bolts'):
                _cp(_here('project', 'src', 'bolts', '__init__.py'), '__init__.py')
                _cp(_here('project', 'src', 'bolts', 'wordcount.py'), 'wordcount.py')
            _mkdir('spouts')
            with _cd('spouts'):
                _cp(_here('project', 'src', 'spouts', '__init__.py'), '__init__.py')
                _cp(_here('project', 'src', 'spouts', 'words.py'), 'words.py')
        _cp(_here('project', 'tasks.py'), 'tasks.py')
        _mkdir('topologies')
        with _cd('topologies'):
            _cp(_here('project', 'topologies', 'wordcount.clj'),
                'wordcount.clj')
        _mkdir('virtualenvs')
        with _cd('virtualenvs'):
            _cp(_here('project', 'virtualenvs', 'wordcount.txt'),
                'wordcount.txt')

    print('Done.\n')
    print(('Try running your topology locally with:\n\n'
           '\tcd {}\n'
           '\tsparse run').format(project_name))

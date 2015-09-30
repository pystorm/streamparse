#!/usr/bin/env python
"""
Copyright 2014-2015 Parsely, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import re
import sys

from setuptools import setup, find_packages

# Get version without importing, which avoids dependency issues
def get_version():
    with open('streamparse/version.py') as version_file:
        return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
                         version_file.read()).group('version')

def readme():
    ''' Returns README.rst contents as str '''
    with open('README.rst') as f:
        return f.read()


install_requires = [
    'invoke>=0.8',
    'fabric',
    'jinja2',
    'requests',
    'prettytable',
    'six>=1.5',
    'simplejson'
]

if sys.version_info.major < 3:
    install_requires.append('contextlib2')

lint_requires = [
    'pep8',
    'pyflakes'
]

if sys.version_info.major < 3:
    tests_require = ['mock', 'nose', 'unittest2']
else:
    tests_require = ['mock', 'nose']

dependency_links = []
setup_requires = []
if 'nosetests' in sys.argv[1:]:
    setup_requires.append('nose')

setup(
    name='streamparse',
    version=get_version(),
    author='Parsely, Inc.',
    author_email='hello@parsely.com',
    url='https://github.com/Parsely/streamparse',
    description=('streamparse lets you run Python code against real-time '
                 'streams of data. Integrates with Apache Storm.'),
    long_description=readme(),
    license='Apache License 2.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sparse = streamparse.cli.sparse:main',
            'streamparse = streamparse.cli.sparse:main'
        ]
    },
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    extras_require={
        'test': tests_require,
        'all': install_requires + tests_require,
        'docs': ['sphinx'] + tests_require,
        'lint': lint_requires
    },
    dependency_links=dependency_links,
    zip_safe=False,
    test_suite='nose.collector',
    include_package_data=True,
)

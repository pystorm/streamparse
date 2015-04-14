'''
This package makes it easier to work with Storm and Python.

:organization: Parsely
'''

from __future__ import absolute_import, print_function, unicode_literals

from . import storm, cmdln, contextmanagers, debug, decorators
from .storm import bolt, component, spout
from .version import __version__, VERSION

__all__ = [
    'storm',
    'cmdln',
    'contextmanagers',
    'debug',
    'decorators',
    'bolt',
    'component',
    'spout',
    '__version__',
    'VERSION',
]

__license__ = """
Copyright 2014 Parsely, Inc.

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

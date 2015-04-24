'''
This package makes it easier to work with Storm and Python.

:organization: Parsely
'''

from __future__ import absolute_import, print_function, unicode_literals

import streamparse.bolt
import streamparse.cmdln
import streamparse.component
import streamparse.contextmanagers
import streamparse.debug
import streamparse.decorators
import streamparse.dsl
import streamparse.spout
import streamparse.storm
from streamparse.version import __version__, VERSION

__all__ = [
    'bolt',
    'cmdln',
    'component',
    'contextmanagers',
    'debug',
    'decorators',
    'dsl',
    'spout',
    'storm',
    '__version__',
    'VERSION',
]

__license__ = """
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

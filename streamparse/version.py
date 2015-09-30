# -*- coding: utf-8 -*-

# Copyright 2014-2015 Parsely, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
This module exists solely for version information so we only have to change it
in one place. Based on the suggestion `here. <http://bit.ly/16LbuJF>`_

:organization: Parsely
'''

__version__ = '2.1.0'
VERSION = tuple(int(x) for x in __version__.split('.'))

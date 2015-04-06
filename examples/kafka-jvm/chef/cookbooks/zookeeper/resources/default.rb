# resources/default.rb
#
# Copyright 2014, Simple Finance Technology Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

actions(:install, :uninstall)
default_action(:install)

attribute :version,     kind_of: String, name_attribute: true
attribute :mirror,      kind_of: String, required: true
attribute :user,        kind_of: String, default: 'zookeeper'
attribute :install_dir, kind_of: String, default: '/opt/zookeeper'
attribute :data_dir,    kind_of: String, default: '/var/lib/zookeeper'
attribute :checksum,    kind_of: String

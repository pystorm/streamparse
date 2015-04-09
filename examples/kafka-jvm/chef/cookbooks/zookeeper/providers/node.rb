# providers/node.rb
#
# Copyright 2013, Simple Finance Technology Corp.
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

def get_zk()
  require 'zookeeper'
  # todo: memoize
  return Zookeeper.new(@new_resource.connect_str)
end

action :create_if_missing do
  zk = get_zk()
  if not zk.stat(:path => @new_resource.path)[:stat].exists?
    zk.create(:path => @new_resource.path, :data => @new_resource.data)
  end
end

action :create do
  zk = get_zk()
  if zk.stat(:path => @new_resource.path)[:stat].exists?
    zk.set(:path => @new_resource.path, :data => @new_resource.data)
  else
    zk.create(:path => @new_resource.path, :data => @new_resource.data)
  end
end

action :delete do
  zk = get_zk()
  zk.delete(:path => @new_resource.path)
end

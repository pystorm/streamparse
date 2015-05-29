#
# Cookbook Name:: streamparse
# Recipe:: default
#
# Copyright 2014, Example Com
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
#

storm_user = node[:storm][:deploy][:user]

# Create log and virtualenv paths ensuring that storm will have write access to
# both

directory node[:streamparse][:log_path] do
  owner storm_user
  group "root"
  mode "0755"
  recursive true
  action :create
end

directory node[:streamparse][:virtualenv_path] do
  owner "vagrant"
  group "root"
  mode "0775"
  recursive true
  action :create
end

# Modify /etc/hosts
bash "add streamparse-box to /etc/hosts" do
  user "root"
  code <<-EOS
  echo "127.0.0.1  streamparse-box" >> /etc/hosts
  EOS
  not_if "grep -q streamparse-box /etc/hosts"
end

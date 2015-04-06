#
# Cookbook Name:: storm
# Recipe:: default
#
# Copyright 2012, Webtrends, Inc.
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

include_recipe "storm"

java_home = node['java']['java_home']

  # control file
  template "#{node['storm']['install_dir']}/bin/supervisor-control" do
    source  "supervisor-control.erb"
    mode  00755
    variables({
      :install_dir => node['storm']['install_dir'],
      :log_dir => node['storm']['log_dir'],
      :java_home => java_home
    })
  end

  # runit service
  runit_service "supervisor" do
    service_name "supervisor"
    options({
      :install_dir => "#{node['storm']['root_dir']}/current",
      :log_dir => node['storm']['log_dir'],
      :user => "storm"
    })
  end

execute "reload_supervisor" do
  command "sv reload supervisor"
  action :nothing
end

service "supervisor"

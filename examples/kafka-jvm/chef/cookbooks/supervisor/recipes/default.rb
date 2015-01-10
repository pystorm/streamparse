#
# Cookbook Name:: supervisor
# Recipe:: default
#
# Copyright 2011, Opscode, Inc.
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

include_recipe "python"

# foodcritic FC023: we prefer not having the resource on non-smartos
if platform_family?("smartos")
  package "py27-expat" do
    action :install
  end
end

python_pip "supervisor" do
  action :upgrade
  version node['supervisor']['version'] if node['supervisor']['version']
end

directory node['supervisor']['dir'] do
  owner "root"
  group "root"
  mode "755"
  recursive true
end

template node['supervisor']['conffile'] do
  source "supervisord.conf.erb"
  owner "root"
  group "root"
  mode "644"
  variables({
    :inet_port => node['supervisor']['inet_port'],
    :inet_username => node['supervisor']['inet_username'],
    :inet_password => node['supervisor']['inet_password'],
    :supervisord_minfds => node['supervisor']['minfds'],
    :supervisord_minprocs => node['supervisor']['minprocs'],
    :supervisor_version => node['supervisor']['version'],
    :socket_file => node['supervisor']['socket_file'],
  })
end

directory node['supervisor']['log_dir'] do
  owner "root"
  group "root"
  mode "755"
  recursive true
end

template "/etc/default/supervisor" do
  source "debian/supervisor.default.erb"
  owner "root"
  group "root"
  mode "644"
  only_if { platform_family?("debian") }
end

init_template_dir = value_for_platform_family(
  ["rhel", "fedora"] => "rhel",
  "debian" => "debian"
)

case node['platform']
when "amazon", "centos", "debian", "fedora", "redhat", "ubuntu"
  template "/etc/init.d/supervisor" do
    source "#{init_template_dir}/supervisor.init.erb"
    owner "root"
    group "root"
    mode "755"
    variables({
      # TODO: use this variable in the debian platform-family template
      # instead of altering the PATH and calling "which supervisord".
      :supervisord => "#{node['python']['prefix_dir']}/bin/supervisord"
    })
  end

  service "supervisor" do
    supports :status => true, :restart => true
    action [:enable, :start]
  end
when "smartos"
  directory "/opt/local/share/smf/supervisord" do
    owner "root"
    group "root"
    mode "755"
  end

  template "/opt/local/share/smf/supervisord/manifest.xml" do
    source "manifest.xml.erb"
    owner "root"
    group "root"
    mode "644"
    notifies :run, "execute[svccfg-import-supervisord]", :immediately
  end

  execute "svccfg-import-supervisord" do
    command "svccfg import /opt/local/share/smf/supervisord/manifest.xml"
    action :nothing
  end

  service "supervisord" do
    action [:enable]
  end
end

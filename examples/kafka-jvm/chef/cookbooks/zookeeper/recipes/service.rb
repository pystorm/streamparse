# recipes/service.rb
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

executable_path = ::File.join(node[:zookeeper][:install_dir],
                              "zookeeper-#{node[:zookeeper][:version]}",
                              'bin',
                              'zkServer.sh')

case node[:zookeeper][:service_style]
when 'upstart'
  template "/etc/default/zookeeper" do
    source 'environment-defaults.erb'
    owner 'zookeeper'
    group 'zookeeper'
    action :create
    mode '0644'
    notifies :restart, 'service[zookeeper]', :delayed
  end
  template "/etc/init/zookeeper.conf" do
    source 'zookeeper.init.erb'
    owner 'root'
    group 'root'
    action :create
    mode '0644'
    notifies :restart, 'service[zookeeper]', :delayed
  end
  service 'zookeeper' do
    provider Chef::Provider::Service::Upstart
    supports :status => true, :restart => true, :reload => true
    action :enable
  end
when 'runit'
  runit_service 'zookeeper' do
    default_logger true
    options({
      exec: executable_path
    })
    action [:enable, :start]
  end
when 'exhibitor'
  Chef::Log.info("Assuming Exhibitor will start up Zookeeper.")
else
  Chef::Log.error("You specified an invalid service style for Zookeeper, but I am continuing.")
end

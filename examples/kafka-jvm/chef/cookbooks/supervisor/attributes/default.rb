#
# Cookbook Name:: supervisor
# Attribute File:: default
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

default['supervisor']['unix_http_server']['chmod'] = '700'
default['supervisor']['unix_http_server']['chown'] = 'root:root'
default['supervisor']['inet_port'] = nil
default['supervisor']['inet_username'] = nil
default['supervisor']['inet_password'] = nil
case node['platform_family']
when "smartos"
  default['supervisor']['dir'] = '/opt/local/etc/supervisor.d'
  default['supervisor']['conffile'] = '/opt/local/etc/supervisord.conf'
else
  default['supervisor']['dir'] = '/etc/supervisor.d'
  default['supervisor']['conffile'] = '/etc/supervisord.conf'
end
default['supervisor']['log_dir'] = '/var/log/supervisor'
default['supervisor']['logfile_maxbytes'] = '50MB'
default['supervisor']['logfile_backups'] = 10
default['supervisor']['loglevel'] = 'info'
default['supervisor']['minfds'] = 1024
default['supervisor']['minprocs'] = 200
default['supervisor']['socket_file'] = '/var/run/supervisor.sock'

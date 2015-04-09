#
# Author:: Gilles Devaux <gilles.devaux@gmail.com>
# Cookbook Name:: supervisor
# Resource:: fcgi
#
# Copyright:: 2011, Formspring.me
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

actions :enable, :disable, :start, :stop, :restart, :reload

def initialize(*args)
  super
  @action = [:enable, :start]
end

attribute :program_name, :kind_of => String, :name_attribute => true
attribute :command, :kind_of => String
attribute :process_name, :kind_of => String, :default => '%(program_name)s'
attribute :numprocs, :kind_of => Integer, :default => 1
attribute :numprocs_start, :kind_of => Integer, :default => 0
attribute :priority, :kind_of => Integer, :default => 999
attribute :autostart, :kind_of => [TrueClass, FalseClass], :default => true
attribute :autorestart, :kind_of => [String, Symbol, TrueClass, FalseClass], :default => :unexpected
attribute :startsecs, :kind_of => Integer, :default => 1
attribute :startretries, :kind_of => Integer, :default => 3
attribute :exitcodes, :kind_of => Array, :default => [0, 2]
attribute :stopsignal, :kind_of => [String, Symbol], :default => :TERM
attribute :stopwaitsecs, :kind_of => Integer, :default => 10
attribute :user, :kind_of => [String, NilClass], :default => nil
attribute :redirect_stderr, :kind_of => [TrueClass, FalseClass], :default => false
attribute :stdout_logfile, :kind_of => String, :default => 'AUTO'
attribute :stdout_logfile_maxbytes, :kind_of => String, :default => '50MB'
attribute :stdout_logfile_backups, :kind_of => Integer, :default => 10
attribute :stdout_capture_maxbytes, :kind_of => String, :default => '0'
attribute :stdout_events_enabled, :kind_of => [TrueClass, FalseClass], :default => false
attribute :stderr_logfile, :kind_of => String, :default => 'AUTO'
attribute :stderr_logfile_maxbytes, :kind_of => String, :default => '50MB'
attribute :stderr_logfile_backups, :kind_of => Integer, :default => 10
attribute :stderr_capture_maxbytes, :kind_of => String, :default => '0'
attribute :stderr_events_enabled, :kind_of => [TrueClass, FalseClass], :default => false
attribute :environment, :kind_of => Hash, :default => {}
attribute :directory, :kind_of => [String, NilClass], :default => nil
attribute :umask, :kind_of => [NilClass, String], :default => nil
attribute :serverurl, :kind_of => String, :default => 'AUTO'
attribute :socket, :kind_of => String, :required => true
attribute :socket_owner, :kind_of => String, :default => nil
attribute :socket_mode, :kind_of => String, :required => '0700'

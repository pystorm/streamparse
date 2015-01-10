#
# Author:: Noah Kantrowitz <noah@opscode.com>
# Cookbook Name:: supervisor
# Provider:: service
#
# Copyright:: 2011, Opscode, Inc <legal@opscode.com>
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

action :enable do
  converge_by("Enabling #{ new_resource }") do
    enable_service
  end
end

action :disable do
  if current_resource.state == 'UNAVAILABLE'
    Chef::Log.info "#{new_resource} is already disabled."
  else
    converge_by("Disabling #{new_resource}") do
      disable_service
    end
  end
end

action :start do
  case current_resource.state
  when 'UNAVAILABLE'
    raise "Supervisor service #{new_resource.name} cannot be started because it does not exist"
  when 'RUNNING'
    Chef::Log.debug "#{ new_resource } is already started."
  when 'STARTING'
    Chef::Log.debug "#{ new_resource } is already starting."
    wait_til_state("RUNNING")
  else
    converge_by("Starting #{ new_resource }") do
      if not supervisorctl('start')
        raise "Supervisor service #{new_resource.name} was unable to be started"
      end
    end
  end
end

action :stop do
  case current_resource.state
  when 'UNAVAILABLE'
    raise "Supervisor service #{new_resource.name} cannot be stopped because it does not exist"
  when 'STOPPED'
    Chef::Log.debug "#{ new_resource } is already stopped."
  when 'STOPPING'
    Chef::Log.debug "#{ new_resource } is already stopping."
    wait_til_state("STOPPED")
  else
    converge_by("Stopping #{ new_resource }") do
      if not supervisorctl('stop')
        raise "Supervisor service #{new_resource.name} was unable to be stopped"
      end
    end
  end
end

action :restart do
  case current_resource.state
  when 'UNAVAILABLE'
    raise "Supervisor service #{new_resource.name} cannot be restarted because it does not exist"
  else
    converge_by("Restarting #{ new_resource }") do
      if not supervisorctl('restart')
        raise "Supervisor service #{new_resource.name} was unable to be started"
      end
    end
  end
end

def enable_service
  e = execute "supervisorctl update" do
    action :nothing
    user "root"
  end

  t = template "#{node['supervisor']['dir']}/#{new_resource.service_name}.conf" do
    source "program.conf.erb"
    cookbook "supervisor"
    owner "root"
    group "root"
    mode "644"
    variables :prog => new_resource
    notifies :run, "execute[supervisorctl update]", :immediately
  end

  t.run_action(:create)
  if t.updated?
    e.run_action(:run)
  end
end

def disable_service
  execute "supervisorctl update" do
    action :nothing
    user "root"
  end

  file "#{node['supervisor']['dir']}/#{new_resource.service_name}.conf" do
    action :delete
    notifies :run, "execute[supervisorctl update]", :immediately
  end
end

def supervisorctl(action)
  cmd = "supervisorctl #{action} #{cmd_line_args} | grep -v ERROR"
  result = Mixlib::ShellOut.new(cmd).run_command
  # Since we append grep to the command
  # The command will have an exit code of 1 upon failure
  # So 0 here means it was successful
  result.exitstatus == 0
end

def cmd_line_args
  name = new_resource.service_name
  if new_resource.process_name != '%(program_name)s'
    name += ':*'
  end
  name
end

def get_current_state(service_name)
  result = Mixlib::ShellOut.new("supervisorctl status").run_command
  match = result.stdout.match("(^#{service_name}(\\:\\S+)?\\s*)([A-Z]+)(.+)")
  if match.nil?
    "UNAVAILABLE"
  else
    match[3]
  end
end

def load_current_resource
  @current_resource = Chef::Resource::SupervisorService.new(@new_resource.name)
  @current_resource.state = get_current_state(@new_resource.name)
end

def wait_til_state(state,max_tries=20)
  service = new_resource.service_name

  max_tries.times do
    return if get_current_state(service) == state

    Chef::Log.debug("Waiting for service #{service} to be in state #{state}")
    sleep 1
  end

  raise "service #{service} not in state #{state} after #{max_tries} tries"

end

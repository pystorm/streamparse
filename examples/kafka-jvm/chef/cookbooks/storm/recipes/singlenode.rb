include_recipe "storm"
include_recipe "supervisor"


template "Storm conf file" do
  path "/home/#{node[:storm][:deploy][:user]}/apache-storm-#{node[:storm][:version]}/conf/storm.yaml"
  source "singlenode.yaml.erb"
  owner node[:storm][:deploy][:user]
  group node[:storm][:deploy][:group]
  mode 0644
end

supervisor_service "storm-nimbus" do
  # action [:enable, :start]
  numprocs 1
  autostart true
  autorestart true
  redirect_stderr true
  stopsignal "KILL"
  user node[:storm][:deploy][:user]
  directory "/home/#{node[:storm][:deploy][:user]}"
  command "/home/#{node[:storm][:deploy][:user]}/apache-storm-#{node[:storm][:version]}/bin/storm nimbus"
end

supervisor_service "storm-supervisor" do
  # action [:enable, :start]
  numprocs 1
  autostart true
  autorestart true
  redirect_stderr true
  stopsignal "KILL"
  user node[:storm][:deploy][:user]
  directory "/home/#{node[:storm][:deploy][:user]}"
  command "/home/#{node[:storm][:deploy][:user]}/apache-storm-#{node[:storm][:version]}/bin/storm supervisor"
end

supervisor_service "storm-drpc" do
  action [:enable, :start]
  numprocs 1
  autostart true
  autorestart true
  redirect_stderr true
  stopsignal "KILL"
  user node[:storm][:deploy][:user]
  directory "/home/#{node[:storm][:deploy][:user]}"
  command "/home/#{node[:storm][:deploy][:user]}/apache-storm-#{node[:storm][:version]}/bin/storm drpc"
end

supervisor_service "storm-logviewer" do
  action [:enable, :start]
  numprocs 1
  autostart true
  autorestart true
  redirect_stderr true
  stopsignal "KILL"
  user node[:storm][:deploy][:user]
  directory "/home/#{node[:storm][:deploy][:user]}"
  command "/home/#{node[:storm][:deploy][:user]}/apache-storm-#{node[:storm][:version]}/bin/storm logviewer"
end

supervisor_service "storm-ui" do
  action [:enable, :start]
  numprocs 1
  autostart true
  autorestart true
  redirect_stderr true
  stopsignal "KILL"
  user node[:storm][:deploy][:user]
  directory "/home/#{node[:storm][:deploy][:user]}"
  command "/home/#{node[:storm][:deploy][:user]}/apache-storm-#{node[:storm][:version]}/bin/storm ui"
end

# bash "Start nimbus" do
#   user node[:storm][:deploy][:user]
#   cwd "/home/#{node[:storm][:deploy][:user]}"
#   code <<-EOH
#   pid=$(pgrep -f backtype.storm.daemon.nimbus)
#   if [ -z $pid ]; then
#     nohup apache-storm-#{node[:storm][:version]}/bin/storm nimbus >>nimbus.log 2>&1 &
#   fi
#   EOH
# end

# bash "Start supervisor" do
#   user node[:storm][:deploy][:user]
#   cwd "/home/#{node[:storm][:deploy][:user]}"
#   code <<-EOH
#   pid=$(pgrep -f backtype.storm.daemon.supervisor)
#   if [ -z $pid ]; then
#     nohup apache-storm-#{node[:storm][:version]}/bin/storm supervisor >>supervisor.log 2>&1 &
#   fi
#   EOH
# end

# bash "Start DRPC" do
#   user node[:storm][:deploy][:user]
#   cwd "/home/#{node[:storm][:deploy][:user]}"
#   code <<-EOH
#   pid=$(pgrep -f backtype.storm.daemon.drpc)
#   if [ -z $pid ]; then
#     nohup apache-storm-#{node[:storm][:version]}/bin/storm drpc >>drpc.log 2>&1 &
#   fi
#   EOH
# end

# bash "Start logviewer" do
#   user node[:storm][:deploy][:user]
#   cwd "/home/#{node[:storm][:deploy][:user]}"
#   code <<-EOH
#   pid=$(pgrep -f backtype.storm.daemon.logviewer)
#   if [ -z $pid ]; then
#     nohup apache-storm-#{node[:storm][:version]}/bin/storm logviewer >>logviewer.log 2>&1 &
#   fi
#   EOH
# end

# bash "Start UI" do
#   user node[:storm][:deploy][:user]
#   cwd "/home/#{node[:storm][:deploy][:user]}"
#   code <<-EOH
#   pid=$(pgrep -f backtype.storm.ui.core)
#   if [ -z $pid ]; then
#     nohup apache-storm-#{node[:storm][:version]}/bin/storm ui >>ui.log 2>&1 &
#   fi
#   EOH
# end

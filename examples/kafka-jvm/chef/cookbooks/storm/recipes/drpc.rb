include_recipe "storm"

template "Storm conf file" do
  path "/home/#{node[:storm][:deploy][:user]}/apache-storm-#{node[:storm][:version]}/conf/storm.yaml"
  source "drpc.yaml.erb"
  owner node[:storm][:deploy][:user]
  group node[:storm][:deploy][:group]
  mode 0644
end

bash "Start drpc" do
  user node[:storm][:deploy][:user]
  cwd "/home/#{node[:storm][:deploy][:user]}"
  code <<-EOH
  pid=$(pgrep -f backtype.storm.daemon.drpc)
  if [ -z $pid ]; then
    nohup apache-storm-#{node[:storm][:version]}/bin/storm drpc >>drpc.log 2>&1 &
  fi
  EOH
end

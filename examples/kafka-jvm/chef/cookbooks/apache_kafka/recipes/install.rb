# encoding: UTF-8
# Cookbook Name:: apache_kafka
# Recipe:: install
#

include_recipe "java" if node["apache_kafka"]["install_java"]

version_tag = "kafka_#{node["apache_kafka"]["scala_version"]}-#{node["apache_kafka"]["version"]}"
download_url = ::File.join(node["apache_kafka"]["mirror"], "#{node["apache_kafka"]["version"]}/#{version_tag}.tgz")
download_path = ::File.join(Chef::Config[:file_cache_path], "#{version_tag}.tgz")

user node["apache_kafka"]["user"] do
  comment node["apache_kafka"]["user"]
  system true
  shell "/bin/false"
end

directory node["apache_kafka"]["install_dir"] do
  recursive true
  owner node["apache_kafka"]["user"]
end

remote_file download_path do
  source download_url
  backup false
  checksum node["apache_kafka"]["checksum"]
  notifies :run, "execute[unzip kafka source]"
  not_if { ::File.exist?(::File.join(node["apache_kafka"]["install_dir"], version_tag)) }
end

execute "unzip kafka source" do
  command "tar -zxvf #{download_path} -C #{node["apache_kafka"]["install_dir"]}"
  not_if { ::File.exist?(::File.join(node["apache_kafka"]["install_dir"], version_tag)) }
end

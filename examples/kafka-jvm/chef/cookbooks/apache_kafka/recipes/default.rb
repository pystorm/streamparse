# encoding: UTF-8
# Cookbook Name:: apache_kafka
# Recipe:: default
#

include_recipe "apache_kafka::install"
include_recipe "apache_kafka::configure"
include_recipe "apache_kafka::service"

#
# Author:: Sean McNamara (<sean.mcnamara@webtrends.com>)
# Cookbook Name:: storm
# Attribute:: default
#
# Copyright 2012, Webtrends Inc.
#

default['storm']['version'] = "0.8.2"
default['storm']['root_dir'] = "/opt/storm"
default['storm']['log_dir'] = "/var/log/storm"
default['storm']['cluster_role'] = ""

# general storm attributes
default['storm']['java_lib_path'] = "/usr/local/lib:/opt/local/lib:/usr/lib"
default['storm']['local_dir'] = "/mnt/storm"
default['storm']['local_mode_zmq'] = "false"
default['storm']['cluster_mode'] = "distributed"

# zookeeper attributes
default['storm']['zookeeper']['port'] = 2181
default['storm']['zookeeper']['root'] = "/storm"
default['storm']['zookeeper']['session_timeout'] = 30000
default['storm']['zookeeper']['retry_times'] = 60
default['storm']['zookeeper']['retry_interval'] = 5000

# supervisor attributes
default['storm']['supervisor']['workers'] = 4
default['storm']['supervisor']['childopts'] = "-Xmx1024m"
default['storm']['supervisor']['worker_start_timeout'] = 120
default['storm']['supervisor']['worker_timeout_secs'] = 30
default['storm']['supervisor']['monitor_frequecy_secs'] = 3
default['storm']['supervisor']['heartbeat_frequency_secs'] = 5
default['storm']['supervisor']['enable'] = true

# worker attributes
default['storm']['worker']['childopts'] = "-Xmx1280m -XX:+UseConcMarkSweepGC -Dcom.sun.management.jmxremote"
default['storm']['worker']['heartbeat_frequency_secs'] = 1
default['storm']['task']['heartbeat_frequency_secs'] = 3
default['storm']['task']['refresh_poll_secs'] = 10
default['storm']['zmq']['threads'] = 1
default['storm']['zmq']['longer_millis'] = 5000

# nimbus attributes
default['storm']['nimbus']['host'] = ""
default['storm']['nimbus']['thrift_port'] = 6627
default['storm']['nimbus']['childopts'] = "-Xmx1024m"
default['storm']['nimbus']['task_timeout_secs'] = 30
default['storm']['nimbus']['supervisor_timeout_secs'] = 60
default['storm']['nimbus']['monitor_freq_secs'] = 10
default['storm']['nimbus']['cleanup_inbox_freq_secs'] = 600
default['storm']['nimbus']['inbox_jar_expiration_secs'] = 3600
default['storm']['nimbus']['task_launch_secs'] = 120
default['storm']['nimbus']['reassign'] = true
default['storm']['nimbus']['file_copy_expiration_secs'] = 600

# ui attributes
default['storm']['ui']['port'] = 8080
default['storm']['ui']['childopts'] = "-Xmx768m"

# drpc attributes
default['storm']['drpc']['port'] = 3772
default['storm']['drpc']['invocations_port'] = 3773
default['storm']['drpc']['request_timeout_secs'] = 600

# transactional attributes
default['storm']['transactional']['zookeeper']['root'] = "/storm-transactional"
default['storm']['transactional']['zookeeper']['port'] = 2181

# topology attributes
default['storm']['topology']['debug'] = false
default['storm']['topology']['optimize'] = true
default['storm']['topology']['workers'] = 1
default['storm']['topology']['acker_executors'] = 1
default['storm']['topology']['acker_tasks'] = "null"
default['storm']['topology']['tasks'] = "null"
default['storm']['topology']['message_timeout_secs'] = 30
default['storm']['topology']['skip_missing_kryo_registrations'] = false
default['storm']['topology']['max_task_parallelism'] = "null"
default['storm']['topology']['max_spout_pending'] = "null"
default['storm']['topology']['state_synchronization_timeout_secs'] = 60
default['storm']['topology']['stats_sample_rate'] = 0.05
default['storm']['topology']['fall_back_on_java_serialization'] = true
default['storm']['topology']['worker_childopts'] = "null"

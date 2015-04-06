maintainer        "Webtrends, Inc."
maintainer_email  "ivan.vonnagy@webtrends.com"
license           "Apache 2.0"
description       "Intalls and configures a Kafka broker"
long_description  IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version           "1.0.20"

depends           "java"
depends           "runit"
depends           "zookeeper"

recipe	"kafka::default",		"Base configuration for kafka"

%w{ debian ubuntu centos redhat fedora scientific amazon }.each do |os|
  supports os
end

attribute "kafka/version",
  :display_name => "Kafka Version",
  :description => "The Kafka version to pull and use",
  :default => "0.7.1"

attribute "kafka/home_dir",
  :display_name => "Kafka Home Directory",
  :description => "Location for Kafka to be located.",
  :default => "/usr/share/kafka"

attribute "kafka/data_dir",
  :display_name => "Kafka Log Directory",
  :description => "Location for Kafka logs.",
  :default => "/usr/share/kafka/kafka-logs"

attribute "kafka/log_dir",
  :display_name => "Kafka log4j Directory",
  :description => ";.",
  :default => "/var/log/kafka"

attribute "kafka/broker_id",
  :display_name => "Kafka Broker Id",
  :description => "The id of the broker. This must be set to a unique integer for each broker. If not set, it defaults to the machine's ip address without the '.'.",
  :default => ""

attribute "kafka/broker_host_name",
  :display_name => "Kafka Host Name",
  :description => "Hostname the broker will advertise to consumers. If not set, kafka will use the host name for the server being deployed to.",
  :default => ""

attribute "kafka/port",
  :display_name => "Kafka Port",
  :description => "The port the socket server listens on.",
  :default => "9092"

attribute "kafka/threads",
  :display_name => "Kafka Threads",
  :description => "The number of processor threads the socket server uses for receiving and answering requests. If not set, defaults to the number of cores on the machine.",
  :default => ""

attribute "kafka/log_flush_interval",
  :display_name => "Kafka Flush Interval",
  :description => "The number of messages to accept before forcing a flush of data to disk.",
  :default => "10000"

attribute "kafka/log_flush_time_interval",
  :display_name => "Kafka Flush Time Interval",
  :description => "The maximum amount of time (ms) a message can sit in a log before we force a flush.",
  :default => "1000"

attribute "kafka/log_flush_scheduler_time_interval",
  :display_name => "Kafka Flush Scheduler Time Interval",
  :description => "The interval (in ms) at which logs are checked to see if they need to be flushed to disk.",
  :default => "1000"

attribute "kafka/log_retention_hours",
  :display_name => "Kafka Log Retention Hours",
  :description => "The minimum age of a log file to be eligible for deletion",
  :default => "168"
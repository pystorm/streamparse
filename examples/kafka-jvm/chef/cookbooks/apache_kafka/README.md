# Apache Kafka Cookbook

Install and configure apache kafka 0.8.2.1.

Default installation assumes a local zookeeper instance (see [SimpleFinance/chef-zookeeper](https://github.com/SimpleFinance/chef-zookeeper)).

Based off the work of [Federico Gimenez Nieto](https://github.com/fgimenez/kafka-cookbook)

## Cookbooks

* `apache_kafka::default`
    - Full default install
* `apache_kafka::install`
    - Install the application, but do not start
    - Useful for wrapper cookbooks that want custom configurations before starting
* `apache_kafka::configure`
    - Create the broker configs
* `apache_kafka::service`
    - Create service upstart scripts

## Usage

Create a single kafka node with a single zookeeper instance on the same host.

```bash
bundle install --path vendor/bundle
bundle exec berks install
bundle exec kitchen converge
bundle exec kitchen login
```

**Create a new kafka topic with 3 partitions**

```bash
sudo /usr/local/kafka/bin/kafka-topics.sh --create --topic event-stream --replication-factor 1 --partitions 3 --zookeeper localhost:2181
# [2015-02-06 00:49:08,721] INFO Topic creation {"version":1,"partitions":{"2":[0],"1":[0],"0":[0]}} (kafka.admin.AdminUtils$)
# Created topic "event-stream".
```

**Verify the new topic exists**

```
sudo /usr/local/kafka/bin/kafka-topics.sh --describe --zookeeper localhost:2181
# Topic:event-stream  PartitionCount:3    ReplicationFactor:1 Configs:
#     Topic: event-stream Partition: 0    Leader: 0   Replicas: 0 Isr: 0
#     Topic: event-stream Partition: 1    Leader: 0   Replicas: 0 Isr: 0
#     Topic: event-stream Partition: 2    Leader: 0   Replicas: 0 Isr: 0
```

**Delete the topic**

```
sudo /usr/local/kafka/bin/kafka-topics.sh --delete --topic event-stream --zookeeper localhost:2181
# Topic event-stream is marked for deletion.
# Note: This will have no impact if delete.topic.enable is not set to true.
```

## Contributing

* Standard PR model with details on why

## Version Control

Major.Minor.Patch managed via thor

**Sample patch bump to master after PR merge**
```
git checkout master
git pull
bundle exec thor version:bump patch
```

## Test Converge

```bash
bundle install --path vendor/bundle
bundle exec berks install
bundle exec kitchen converge
```

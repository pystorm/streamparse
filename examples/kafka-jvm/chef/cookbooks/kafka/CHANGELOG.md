## 1.0.20
* Added better check is zookeeper_pairs contains anything to decide is
  kafka should register in zookeeper. This is needed for collection-1.1
  end state work.

## 1.0.19
* Use a notify from the download of the Kafka build to the untar so we don't untar over the server contents on every run
* Switch from an rdoc to a md for the README.

## 1.0.18
* If we use create_if_missing and checksum then only create_if_missing gets used.  We want to use checksum
* Remove the deletion of the tarball

## 1.0.17
* Don't fall back to attributes if the search for ZK nodes fails

## 1.0.16
* Start Kafka at the end of the recipe
* Use objects instead of strings where appropriate (reduce food critic warnings)

## 1.0.15
* Adding checksum attribute

## 1.0.14
* Make JMX port an attribute within the cookbook instead of hardcoding to 9999

## 1.0.13
* Changed the num_partitions to have a default of 1, and set the partitions
  to something higher per env.

## 1.0.12
* Added an attribute to allow for setting the number of partitions globally,
  and set that value to 4 as the default.

## 1.0.11
* Allow changing the Kafka local user / group
* Log4J logging levels are now controlled via log4j_logging_level attribute

## 1.0.10
* Remove broker chroot prefix from zk.connect string

## 1.0.9
* Make 0.7.1 the default not 0.7.0

## 1.0.8
* Added broker chroot prefix for zk.connect string

## 1.0.6 - 1.0.7
* Added changes to support kafka 0.7.1

## 1.0.5
* Added template to create a collectd plugin for kafka JMX objects.

## 1.0.4
* Fixed the creation the bin dir.

## 1.0.3
* Added logic to prevent kafka from being nuked each time Chef is run. A manual delete of the kafka install folder will trigger a re-deploy.

## 1.0.2
* Set default broker_id to nil and if not set will use the ip address without the '.'
* Set the default broker_host_name to nil and if not set will use the server hostname
* Fixed log4j.properties problems

## 1.0.1

* Use /opt/kafka as the default intall dir
* Use /var/kafka as the default data dir
* Remove the unnecessary platform case statement from the attributes file
* Remove the attributes for user/group. Always run as kafka user/group
* Remove tarball from the cookbook
* Don't give kafka user a home directory or a valid shell
* Fix runit script to work
* Pull the source file down from a remote URL and not the cookbook
* Use more restrictive permissions on config files
* Use remote zookeeper nodes
* Don't hardcode the broker ID

## 1.0.0
* Initial release with a changelog
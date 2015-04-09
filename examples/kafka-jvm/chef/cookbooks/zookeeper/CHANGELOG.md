# CHANGELOG for zookeeper
This file is used to list changes made in each version of zookeeper.

## 2.5.1
* Report `zookeeper_config` as updated only if zoo.cfg is updated (#110)
* Fix `zk_installed` return value (#113)
* Fix docs (#114, #115)
* Fix for undefined new method error (#116)
* Always install `build-essential`, regardless of usage of `java` cookbook

## 2.5.0
* Allow configurable `data_dir` parameter for Zookeeper data directory location
  (contributed by @eherot)

## 2.4.3
* Fix erroneous attribute reference

## 2.4.2
* Allow pre-installed Java (contributed by @solarce)

## 2.4.1
* Fixed recipe call (contributed by @solarce)

## 2.4.0
* Split out config rendering to separate recipe (contributed by @solarce)

## 2.3.0
* Split out installation to a separate recipe (contributed by @Gazzonyx)

## 2.2.1
* Set minimum build-essential version for RHEL support (contributed by
  @Gazzonyx)

## 2.2.0
* Upstart support (contributed by @solarce)

## 2.1.1
* Added a service recipe which can be run and activated using new service_style
  attribute.

## 2.1.0
* A basic configuration is rendered by default.
* Clarify some points in the README about zookeeper\_config

## 2.0.0
* Exhibitor cookbook factored out (contributed by @wolf31o2)
* Zookeeper recipe rewritten as LWRP
* Documentation updated slightly
* Tested and verified and (hopefully) as backwards-compatible as possible
  - Being a full version bump, there are no backwards-compatibility promises
* TODO
  - Better documentation
  - `zookeeper_service` resource
  - `zookeeper_config` resource
  - Better tests
  - Swap out "community" Java

## 1.7.4
* Force build-essential to run at compile time (contributed by @davidgiesberg)

## 1.7.3
* Bugfix for attribute access (fixes 1.7.2 bug)

## 1.7.2
* Move ZK download location calculation to recipe to eliminate ordering bug

## 1.7.1
* Test-kitchen support added
* Patch installed to support CentOS platform

## 1.7.0
* Switched to Runit for process supervision (contributed by @gansbrest)
* DEPRECATION WARNING: Upstart is no longer supported and has been removed
* Re-add check-local-zk.py script but punt on utilizing it
* This means we recommend staying on 1.6.1 or below if you use Upstart
* In the meantime, we are working on a strategy to integrate this functionality
  into the Runit script, to support dependent services

## 1.6.0
* Attribute overrides to defaultconfig should now work (contributed by @trane)

## 1.5.1
* Add correct (Apache v2) license to metadta.rb (#61)

## 1.5.0
* Add logic to download existing exhibitor jar

## 1.4.10
* changes: Skip S3 credentials file if AWS credentials are not provided

### OpsWorks related changes
* Moved property files from inaccessible chef dir to exhibitor install dir.
* Logged output to syslog.
* Added option to set exhibitor/amazon log level

## 1.4.9
* Added: s3credentials template to assist with --configtype s3

## 1.4.8
* Added config hook and default for servers-spec setting
* bugfix: cache permission denied error on exhibitor jar move
* bugfix: ZooKeeper install tar cache EACCES error

## 1.4.7
* bugfix: zk_connect_str actually returned when chroot passed.
* forward zk port in vagrant

## 1.4.4

* fix for backwards compatibility with ruby 1.8.7

## 0.1.0:

* Initial release of zookeeper

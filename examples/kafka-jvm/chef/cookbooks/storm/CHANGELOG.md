## 1.2.6
* Cleaned up food critic warnings
* Made default version 0.8.2

## 1.2.5
* Fixing path in supervisor runit script

## 1.2.4
* Added conf creation to the list of dirs to creat

## 1.2.3
* Changed default ZooKeeper Settings

## 1.2.2
* Removed deploy_build block entirely 
* Changed remote_file to use :create_if_missing

## 1.2.1
* Updated run_list to recipe for determing nimbus node

## 1.2.0
* Changes to set node data for topologies to use

## 1.1.0
* Added runit include

## 1.0.34
* Used joshes correct changes

## 1.0.33
* Changed template to be current
* Changed the service reload to not be immediate

## 1.0.31
* Added support for new runit version.

## 1.0.30
* Changed supervisor control script which would prevent a supervisor from
  starting because worker processes were already running. It can happen
  that a supervisor will die but the workers not, then runit will no
  longer be able to start the supervisor. This fix should prevent that.

## 1.0.29
* Changed the default worker memory size.

## 1.0.28
* Add support for Ubuntu to the metadata
* Add a Readme
* Increase file handler limit for nimbus to 20,000

## 1.0.27
* Bump the file handler limit on the webui to 1024. The limit was already increased on Nimbus

## 1.0.26
* Cleans out the state of only the previous runs supervisors, but not the workers.
  Removing the workers state caused supsequent supervisors to bitch about not
  being able to remove the pid files from /mnt/storm/work/XXX/pids without
  end.

## 1.0.25
* Remove the force-yes for installing packages.  This was needed due to the old setup of our apt repo
* Adding default attribute for the storm version

## 1.0.24
* Removed the 'force-stop' call since it is not suported by the 'service' command

## 1.0.23
* Added undeploy scripts.

## 1.0.22
* Address food critic warnings
* Remove the ulimits template since this doesn't work in Ubuntu and was replaced with a ulimit statement in 1.0.21
* Don't fall back to attributes if the Zookeeper node search fails

## 1.0.21
* Add ulimit statement to the runit script for nimbus to increase the file limit to 10240

## 1.0.20
* Add log_dir and install_dir as default attributes

## 1.0.19
* Changed the limits.d file to bump the open file limit for any user

## 1.0.18
* Removed Webtrends specific attributes

## 1.0.17
* Change nimbus and storm ui start/stop scripts to kill related
  processes

## 1.0.16
* Increase file limits for the storm user from 1024 to 32k

## 1.0.15
* Someone changes something

## 1.0.14
* Create a link /opt/storm/current that points to the current version

## 1.0.13
* Some Sean changes

## 1.0.12
* added fallback method of getting zookeeper servers from attributes

## 1.0.10
* storm 0.7.2 as default
* storm pulled from internal repo now, no longer stored as a cookbook file

## 1.0.9
* Force install the prereq packages to resolve issues with unsigned packages
* Add every possible attribute ever, but don't use them *yet*

## 1.0.8
* cookbook re-write
* using debs for zeromq and jzmq

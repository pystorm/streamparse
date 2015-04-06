Description
===========
Installs Twitter's Storm distributed computation platform.  Includes recipes for installing
both the Nimbus / Web UI component and the Supervisor component.

Requirements
============
* Ubuntu 10.04 / 12.04
* May function on other distributions, but has not been tested

* java cookbook
* runit cookbook

Attributes
==========

Usage
=====

This recipe relies on two setup components that need to be noted as they are not used
in many (or any) community cookbooks.

Role Based Cluster Setup:
This cookbook relies on a cluster identification role to allow more than one storm cluster
to run in a single Chef environment, while not breaking Chef search.  Create a role with
a name of your choosing.  The role may be left empty or you may use it to apply the your
application's topology and all necessary JARs within your topology.  You will need to
specify the name of this role using the node attribute ['storm']['cluster_role'], which
is empty by default.  You will need to apply this cluster role to both supervisor and
the nimbus/UI node in your cluster

Deploy Flag:
This cookbook uses a deploy flag to prevent the application from deploying unless desired
and allows for an undeploy recipe to run prior to the deploy.  The deploy recipe will also
cleanup the state of storm and is sufficient to wipe clean any topology deploy, although
it does not stop the actual topology (that's in the works).  Once you've applied the
supervisor or nimbus recipes to a node you need to have "deploy_build=true" set in your
shell.  "sudo deploy_build=true chef-client" can be used to set the environment variable
and run Chef in a single command.
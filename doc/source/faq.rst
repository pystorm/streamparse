Frequently Asked Questions (FAQ)
================================

**Errors while running streamparse:**

* `I received an "InvalidClassException" while submitting my topology, what do I do?`_



I received an "InvalidClassException" while submitting my topology, what do I do?
---------------------------------------------------------------------------------

If the Storm version dependency you specify in your ``project.clj`` file is
different from the version of Storm running on your cluster, you'll get an
error in Storm's logs that looks something like the following when you submit
your topology::

    2014-07-07 02:30:27 b.s.d.executor [INFO] Finished loading executor __acker:[2 2]
    2014-07-07 02:30:27 b.s.d.executor [INFO] Preparing bolt __acker:(2)
    2014-07-07 02:30:27 b.s.d.executor [INFO] Prepared bolt __acker:(2)
    2014-07-07 02:30:27 b.s.d.executor [INFO] Loading executor count-bolt:[4 4]
    2014-07-07 02:30:27 b.s.d.worker [ERROR] Error on initialization of server mk-worker
    java.lang.RuntimeException: java.io.InvalidClassException: backtype.storm.task.ShellBolt; local class incompatible: stream classdesc serialVersionUID = 7728860535733323638, local class serialVersionUID = -6826504627767683830
        at backtype.storm.utils.Utils.deserialize(Utils.java:93) ~[storm-core-0.9.2-incubating.jar:0.9.2-incubating]
        at backtype.storm.utils.Utils.getSetComponentObject(Utils.java:235) ~[storm-core-0.9.2-incubating.jar:0.9.2-incubating]
        at backtype.storm.daemon.task$get_task_object.invoke(task.clj:73) ~[storm-core-0.9.2-incubating.jar:0.9.2-incubating]
        at backtype.storm.daemon.task$mk_task_data$fn__3061.invoke(task.clj:180) ~[storm-core-0.9.2-incubating.jar:0.9.2-incubating]
        at backtype.storm.util$assoc_apply_self.invoke(util.clj:816) ~[storm-core-0.9.2-incubating.jar:0.9.2-incubating]
        at backtype.storm.daemon.task$mk_task_data.invoke(task.clj:173) ~[storm-core-0.9.2-incubating.jar:0.9.2-incubating]
        at backtype.storm.daemon.task$mk_task.invoke(task.clj:184) ~[storm-core-0.9.2-incubating.jar:0.9.2-incubating]
        at backtype.storm.daemon.executor$mk_executor$fn__5510.invoke(executor.clj:321) ~[storm-core-0.9.2-incubating.jar:0.9.2-incubating]
        at clojure.core$map$fn__4207.invoke(core.clj:2485) ~[clojure-1.5.1.jar:na]

Check to ensure the version of Storm in your ``project.clj`` file matches the
Storm version running on your cluster, then try resubmitting your topology.

.. code-block:: clojure

  (defproject my-project "0.0.1-SNAPSHOT"
    :source-paths ["topologies"]
    :resource-paths ["_resources"]
    :target-path "_build"
    :min-lein-version "2.0.0"
    :jvm-opts ["-client"]
    :dependencies  [[org.apache.storm/storm-core "0.9.1-incubating"] ;; this should match your Storm cluster
                    [com.parsely/streamparse "0.0.3-SNAPSHOT"]]
    :jar-exclusions     [#"log4j\.properties" #"backtype" #"trident" #"META-INF" #"meta-inf" #"\.yaml"]
    :uberjar-exclusions [#"log4j\.properties" #"backtype" #"trident" #"META-INF" #"meta-inf" #"\.yaml"]
  )

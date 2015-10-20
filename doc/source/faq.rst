Frequently Asked Questions (FAQ)
================================

General Questions
-----------------

* `Why use streamparse?`_
* `Is streamparse compatible with Python 3?`_
* `How can I contribute to streamparse?`_
* `How do I trigger some code before or after I submit my topology?`_
* `How should I install streamparse on the cluster nodes?`_
* `Should I install Clojure?`_

Why use streamparse?
~~~~~~~~~~~~~~~~~~~~

To lay your Python code out in topologies which can be automatically
parallelized in a Storm cluster of machines. This lets you scale your
computation horizontally and avoid issues related to Python's GIL. See
:ref:`parallelism`.

Is streamparse compatible with Python 3?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, streamparse is fully compatible with Python 3 starting with version 3.3
which we use in our `unit tests`_.

.. _unit tests: https://github.com/Parsely/streamparse/blob/master/.travis.yml

How can I contribute to streamparse?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Thanks for your interest in contributing to streamparse. We think
you'll find the core maintainers great to work with and will help you along the
way when contributing pull requests.

If you already know what you'd like to add to streamparse then by all means,
feel free to submit a pull request and we'll review it.

If you're unsure about how to contribute, check out our `open issues`_ and find
one that looks interesting to you (we particularly need help on all issues
marked with the "help wanted" label).

If you're not sure how to start or have some questions, shoot us an email in
the `streamparse user group`_ and we'll give you a hand.

From there, get to work on your fix and submit a pull request when ready which
we'll review.

.. _open issues: https://github.com/Parsely/streamparse/issues?state=open
.. _streamparse user group: https://groups.google.com/forum/#!forum/streamparse

How do I trigger some code before or after I submit my topology?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After you create a streamparse project using ``sparse quickstart``, you'll have
both a ``tasks.py`` in that directory as well as ``fabric.py``. In either of
these files, you can specify two functions: ``pre_submit`` and ``post_submit``
which are expected to accept three arguments:

* ``topology_name``: the name of the topology being submitted
* ``env_name``: the name of the environment where the topology is being
  submitted (e.g. ``"prod"``)
* ``env_config``: the relevant config portion from the ``config.json`` file for
  the environment you are submitting the topology to

Here is a sample ``tasks.py`` file that sends a message to IRC after a topology
is successfully submitted to prod.

.. code-block:: python

    # my_project/tasks.py
    from __future__ import absolute_import, print_function, unicode_literals

    from invoke import task, run
    from streamparse.ext.invoke import *


    def post_submit(topo_name, env_name, env_config):
        if env_name == "prod":
            write_to_irc("Deployed {} to {}".format(topo_name, env_name))


How should I install streamparse on the cluster nodes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

streamparse assumes your Storm servers have Python, pip, and virtualenv
installed.  After that, the installation of all required dependencies (including
streamparse itself) is taken care of via the `config.json` file for the
streamparse project and the sparse submit command. See :ref:`Remote Deployment`
for more information.

Should I install Clojure?
~~~~~~~~~~~~~~~~~~~~~~~~~

No, the Java requirements for streamparse are identical to that of Storm itself.
Storm requires Java and `bundles Clojure as a requirement`_, so you do not need
to do any separate installation of Clojure.  You just need Java on all Storm
servers.

.. _bundles Clojure as a requirement: https://github.com/apache/storm/blob/5383ac375cb2955e3247d485e46f1f58bff62810/pom.xml#L320-L322

Errors While Running streamparse
--------------------------------

* `I received an "InvalidClassException" while submitting my topology, what do I do?`_


I received an "InvalidClassException" while submitting my topology, what do I do?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    :dependencies  [[org.apache.storm/storm-core "0.9.4"] ;; this should match your Storm cluster
                    [com.parsely/streamparse "0.0.4-SNAPSHOT"]]
    :jar-exclusions     [#"log4j\.properties" #"backtype" #"trident" #"META-INF" #"meta-inf" #"\.yaml"]
    :uberjar-exclusions [#"log4j\.properties" #"backtype" #"trident" #"META-INF" #"meta-inf" #"\.yaml"]
  )

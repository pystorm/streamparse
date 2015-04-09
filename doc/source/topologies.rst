Topologies
==========

Clojure Quick Reference Guide
-----------------------------
Topologies in streamparse are defined using Clojure. Here is a quick overview
so you don't get lost.

Function definitions
    ``(defn fn-name [options] expressions)`` defines a function called
    ``fn-name`` that takes ``options`` as an argument and evaluates each of the
    ``expressions``, treating the last evaluated expression as the return value
    for a function.

Keyword arguments
    In Clojure, keyword arguments are specified using paired-up positional
    arguments. Thus ``:p 2`` is the ``p`` keyword set to value ``2``.

List
    ``[val1 val2 ... valN]`` defines a list of N values.

Map
    ``{"key-1" val1 "key-2" val2 ... "key-N" valN}`` is a mapping of key-value
    pairs.

Comments
    Anything after ``;;`` is a line comment.

For Python programmers, Clojure can be a little tricky in that whitespace is
not significant, and ``,`` is treated as whitespace. This means ``[val1 val2]``
and ``[val1, val2]`` are identical lists. Function definitions can similarly
take up multiple lines.

.. code-block:: clojure

    (defn fn-name [options]
        expression1
        expression2
        ;; ...
        expressionN
        ;; the value of expressionN is the returned value
    )

Topology Files
--------------
A topology file describes your topology in terms of Directed Acyclic Graph (DAC)
of Storm components, namely Bolts and Spouts. It uses the
`Clojure DSL <http://storm.apache.org/documentation/Clojure-DSL.html>`_ for
this, along with some utility functions streamparse provides.

Topology files are located in ``topologies`` in your streamparse project folder.
There can be any number of topology files for your project in this directory.

* topologies/my-topology.clj
* topologies/my-other-topology.clj
* topologies/my-third-topology.clj

So on and so forth.

A sample ``my-topology.clj``, would start off importing the streamparse
Clojure DSL functions.

.. code-block:: clojure

    (ns my-topology
      (:use     [streamparse.specs])
      (:gen-class))

Notice the ``my-topology`` matches the name of the file. The next line is the
import of the streamparse utility functions.

You could optionally avoid all of the streamparse-provided helper functions and
import your own functions or the Clojure DSL for Storm directly.

.. code-block:: clojure

    (ns my-topology
      (:use     [backtype.storm.clojure])
      (:gen-class))

In the next part of the file, we setup a topology definition, also named
``my-topology`` (matching the ``ns`` line and filename). This definition is
actually a Clojure function that takes the topology options as a single map
argument. This function returns a list of 2 maps -- a spout map, and a bolt map.
These two maps define the DAG that is your topology.

.. code-block:: clojure

    (defn my-topology [options]
       [
        ;; spout configuration
        {"my-python-spout" (python-spout-spec
              ;; topology options passed in
              options
              ;; python class to run
              "spouts.myspout.MySpout"
              ;; output specification, what named fields will this spout emit?
              ["data"]
              ;; configuration parameters, can specify multiple or none at all
              )
       }


        ;; bolt configuration
        {"my-python-bolt" (python-bolt-spec
              ;; topology options pased in
              options
              ;; inputs, where does this bolt receive its tuples from?
              {"my-python-spout" :shuffle}
              ;; python class to run
              "bolts.mybolt.MyBolt"
              ;; output specification, what named fields will this spout emit?
              ["data" "date"]
              ;; configuration parameters, can specify multiple or none at all
              :p 2
              )
        }
      ]
    )

Shell Spouts and Bolts
----------------------

The `Clojure DSL <http://storm.apache.org/documentation/Clojure-DSL.html>`_
provides the ``shell-bolt-spec`` and ``shell-spout-spec``
functions to handle bolts in non-JVM languages.

The ``shell-spout-spec`` takes at least 2 arguments:

1. The command line program to run (as a list of arguments)
2. A list of the named fields the spout will output
3. Any optional keyword arguments

.. code-block:: clojure

    "my-shell-spout" (shell-spout-spec
        ;; Command to run
        ["python" "spout.py"]
        ;; output specification, what named fields will this spout emit?
        ["data"]
        ;; configuration parameters, can specify multiple or none at all
        :p 2
    )


The ``shell-bolt-spec`` takes at least 3 arguments:

1. A map of the input spouts and their groupings
2. The command line program to run (as a list of arguments)
3. A list of the named fields the spout will output
4. Any optional keyword arguments

.. code-block:: clojure

    "my-shell-bolt" (shell-bolt-spec
        ;; input spouts and their groupings
        {"my-shell-spout" :shuffle}
        ;; Command to run
        ["bash" "mybolt.sh"]
        ;; output specification, what named fields will this spout emit?
        ["data"]
        ;; configuration parameters, can specify multiple or none at all
        :p 2
    )


Python Spouts and Bolts
-----------------------

The example topology above, and the ``sparse quickstart wordcount`` project
utilizes the ``python-spout-spec`` and ``python-bolt-spec`` provided by the
``streamparse.specs`` import statement.

``(python-spout-spec ...)`` and ``(python-bolt-spec ...)`` are just convenience
functions provided by streamparse for creating topology components. They are
simply wrappers around ``(shell-spout-spec ...)`` and ``(shell-bolt-spec ...)``.

The ``python-spout-spec`` takes at least 3 arguments:

1. ``options`` - the topology options array passed in
2. The full path to the class to run. ``spouts.myspout.MySpout`` is actually the
   ``MySpout`` class in ``src/spouts/myspout.py``
3. A list of the named fields the spout will output
4. Any optional keyword arguments, such as parallelism ``:p 2``


The ``python-bolt-spec`` takes at least 4 arguments:

1. ``options`` - the topology options array passed in
2. A map of the input spouts and their groupings (See below)
3. The full path to the class to run. ``bolts.mybolt.MyBolt`` is actually the
   ``MyBolt`` class in ``src/bolts/mybolt.py``
4. A list of the named fields the spout will output
5. Any optional keyword arguments, such as parallelism ``:p 2``


Groupings
^^^^^^^^^

Storm offers comprehensive options for `stream groupings
<http://storm.incubator.apache.org/documentation/Concepts.html#stream-groupings>`_,
but you will most commonly use a **shuffle** or **fields** grouping:

* **Shuffle grouping**: Tuples are randomly distributed across the bolt’s tasks
  in a way such that each bolt is guaranteed to get an equal number of tuples.
* **Fields grouping**: The stream is partitioned by the fields specified in the
  grouping. For example, if the stream is grouped by the “user-id” field,
  tuples with the same “user-id” will always go to the same task, but tuples
  with different “user-id”’s may go to different tasks.


Running Topologies
------------------

When you run a topology either locally or by submitting to a cluster,
streamparse will

1. Compile your .clj topology file
2. Execute the Clojure code by invoking your topology function, passing it the
   ``options`` map
3. Get the DAG defined by the topology and pass it into the Storm Java interop
   classes like StormSubmitter and LocalCluster
4. Run/submit your topology

If you invoked streamparse with ``sparse run``, your code is executed directly
from the ``src/`` directory.

If you submitted to a cluster, streamparse uses ``lein`` to compile the ``src``
directory into a jar file, which is run on the cluster. Lein uses the
``project.clj`` file located in the root of your project. This file is a
standard lein project file and can be customized according to your needs.



Topologies
==========


Starting off
-----------------
Topology files are located in ``topologies`` in your streamparse project folder.
There can be any number of topology files for your project in this directory.

* topologies/my-topology.clj
* topologies/my-other-topology.clj
* topologies/my-third-topology.clj

So on and so forth.

Your topology file that describes the Directed Acyclic Graph (DAG) that will 
be run in Storm.

Looking at ``my-topology.clj``, we start off with importing the streamparse
Clojure DSL functions

.. code-block:: clojure

    (ns my-topology
      (:use     [streamparse.specs])
      (:gen-class))

Notice the ``my-topology`` matches the name of the file. We then have the
import function.

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
        {"my-spout" (python-spout-spec
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
        {"my-bolt" (python-bolt-spec
              ;; topology options pased in
              options
              ;; inputs, where does this bolt receive its tuples from?
              {"my-spout" :shuffle}
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


Python Spouts and Bolts
-----------------------

The example topology above, and the ``sparse quickstart wordcount`` project 
utilizes the ``python-spout-spec`` and ``python-bolt-spec`` provided by the 
``streamparse.specs`` import statement.

The ``python-spout-spec`` takes at least 3 arguments:

1. ``options`` - the topology options array passed in
2. The full path to the class to run. ``spouts.myspout.MySpout`` is actually the ``MySpout`` class in ``src/spouts/myspout.py``
3. A list of the named fields the spout will output
4. Any optional configuration parameters, such as parallelism


The ``python-bolt-spec`` takes at least 4 arguments:

1. ``options`` - the topology options array passed in
2. A map of the input spouts and their groupings (See below)
3. The full path to the class to run. ``bolts.mybolt.MyBolt`` is actually the ``MyBolt`` class in ``src/bolts/mybolt.py``
4. A list of the named fields the spout will output
5. Any optional configuration parameters, such as parallelism


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
2. Execute the Clojure code by invoking your topology function, passing it the ``options`` map
3. Get the DAG defined by the topology and pass it into the Storm Java interop classes like StormSubmitter and LocalCluster
4. Run/submit your topology

If you invoked streamparse with ``sparse run``, your code is executed directly 
from the ``src/`` directory.

If you submitted to a cluster, streamparse uses ``lein`` to compile the ``src`` 
directory into a jar file, which is run on the cluster. Lein uses the 
``project.clj`` file located in the root of your project. This file is a 
standard lein project file and can be customized according to your needs.



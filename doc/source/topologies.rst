.. versionadded:: 3.0.0

Topology DSL
============

To simplify the process of creating Storm topologies, streamparse features a
Python Topology `DSL <https://en.wikipedia.org/wiki/Domain-specific_language>`_.
It lets you specify topologies as complex as those you can in `Java <https://github.com/apache/storm/blob/07629c1f898ebb0cedcc19e15e4813692b6a9345/examples/storm-starter/src/jvm/org/apache/storm/starter/WordCountTopology.java>`_
or `Clojure <https://github.com/apache/storm/blob/07629c1f898ebb0cedcc19e15e4813692b6a9345/examples/storm-starter/src/clj/org/apache/storm/starter/clj/word_count.clj>`,
but in concise, readable Python.

Topology Files
--------------

A topology file describes your topology in terms of Directed Acyclic Graph
(DAG) of Storm components, namely `bolts` and `spouts`.

Topology files are located in ``topologies`` in your streamparse project folder.
There can be any number of topology files for your project in this directory.

* ``topologies/my_topology.py``
* ``topologies/my_other_topology.py``
* ``topologies/my_third_topology.py``

So on and so forth.

Creating a Topology in Python
-----------------------------

1.  Create a Python module with the name of your topology (e.g., ``wordcount.py``) inside your projects ``topologies`` directory.
2.	Add a class that inherits from :class:`streamparse.Topology` to your file that specifies the bolts and spouts in your topology and their connections.

  	.. literalinclude:: ../../examples/redis/topologies/wordcount_mem.py
  		:language: python


Running Topologies
------------------

What Streamparse Does
^^^^^^^^^^^^^^^^^^^^^

When you run a topology either locally or by submitting to a cluster,
streamparse will

1. Bundle all of your code into a JAR
2. Build a Thrift Topology struct our of your Python topology definition.
3. Pass the Thrift Topology struct to Nimbus on your Storm cluster.

If you invoked streamparse with ``sparse run``, your code is executed directly
from the ``src/`` directory.

If you submitted to a cluster with ``sparse submit``, streamparse uses ``lein``
to compile the ``src`` directory into a jar file, which is run on the
cluster. Lein uses the ``project.clj`` file located in the root of your
project. This file is a standard lein project file and can be customized
according to your needs.

.. _dealing-with-errors:

Dealing With Errors
^^^^^^^^^^^^^^^^^^^

When detecting an error, bolt code can call its :meth:`~streamparse.Bolt.fail`
method in order to have Storm call the respective spout's
:meth:`~streamparse.Spout.fail` method. Known error/failure cases result in
explicit callbacks to the spout using this approach.

Exceptions which propagate without being caught will cause the component to
crash. On ``sparse run``, the entire topology will stop execution. On a running
cluster (i.e. ``sparse submit``), Storm will auto-restart the crashed component
and the spout will receive a :meth:`~streamparse.Spout.fail` call.

If the spout's fail handling logic is to hold back the tuple and not re-emit
it, then things will keep going. If it re-emits it, then it may crash that
component again. Whether the topology is tolerant of the failure depends on how
you implement failure handling in your spout.

Common approaches are to:

* Append errant tuples to some sort of error log or queue for manual inspection
  later, while letting processing continue otherwise.
* Attempt 1 or 2 retries before considering the tuple a failure, if the error
  was likely an transient problem.
* Ignore the failed tuple, if appropriate to the application.


.. _parallelism:

Parallelism and Workers
-----------------------

**In general, use the ``par`` "parallelism hint" parameter per spout and bolt in
your configuration to control the number of Python processes per component.**

Reference: `Understanding the Parallelism of a Storm Topology <https://storm.apache.org/documentation/Understanding-the-parallelism-of-a-Storm-topology.html>`_

Storm parallelism entities:

* A `worker process` is a JVM, i.e. a Java process.
* An `executor` is a thread that is spawned by a worker process.
* A `task` performs the actual data processing.
  (To simplify, you can think of it as a Python callable.)

Spout and bolt specs take a ``par`` keyword to provide a parallelism hint to
Storm for the number of executors (threads) to use for the given spout/bolt;
for example, ``par=2`` is a hint to use two executors. Because streamparse
implements spouts and bolts as independent Python processes, setting ``par=N``
results in N Python processes for the given spout/bolt.

Many streamparse applications will need only to set this parallelism hint to
control the number of resulting Python processes when tuning streamparse
configuration. For the underlying topology workers, streamparse sets a default
of 2 workers, which are independent JVM processes for Storm. This allows a
topology to continue running when one worker process dies; the other is around
until the dead process restarts.

Both ``sparse run`` and ``sparse sumbit`` accept a ``-p N`` command-line flag
to set the number of topology workers to N. For convenience, this flag also
sets the number of `Storm's underlying messaging reliability
<https://storm.apache.org/documentation/Guaranteeing-message-processing.html>`_
`acker bolts` to the same N value. In the event that you need it (and you
understand Storm ackers), use the ``-a`` and ``-w`` command-line flags instead
of ``-p`` to control the number of acker bolts and the number of workers,
respectively. The ``sparse`` command does not support Storm's rebalancing
features; use ``sparse submit -f -p N`` to kill the running topology and
redeploy it with N workers.

Note that `the underlying Storm thread implementation <https://storm.apache.org/2012/08/02/storm080-released.html>`_,
`LMAX Disruptor <http://lmax-exchange.github.io/disruptor/>`_, is designed with
high-performance inter-thread messaging as a goal. Rule out Python-level issues
when tuning your topology:

* bottlenecks where the number of spout and bolt processes are out of balance
* serialization/deserialization overhead of more data emitted than you need
* slow routines/callables in your code


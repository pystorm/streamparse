.. versionadded:: 3.0.0


Topologies
==========

Storm topologies are described as a Directed Acyclic Graph (DAG) of Storm
components, namely `bolts` and `spouts`.

.. _topology_dsl:

Topology DSL
------------

To simplify the process of creating Storm topologies, streamparse features a
Python Topology `DSL <https://en.wikipedia.org/wiki/Domain-specific_language>`_.
It lets you specify topologies as complex as those you can in `Java <https://github.com/apache/storm/blob/07629c1f898ebb0cedcc19e15e4813692b6a9345/examples/storm-starter/src/jvm/org/apache/storm/starter/WordCountTopology.java>`_
or `Clojure <https://github.com/apache/storm/blob/07629c1f898ebb0cedcc19e15e4813692b6a9345/examples/storm-starter/src/clj/org/apache/storm/starter/clj/word_count.clj>`_,
but in concise, readable Python.

Topology files are located in ``topologies`` in your streamparse project folder.
There can be any number of topology files for your project in this directory.

* ``topologies/my_topology.py``
* ``topologies/my_other_topology.py``
* ``topologies/my_third_topology.py``
* ...

A valid :class:`~streamparse.Topology` may only have :class:`~streamparse.Bolt`
and :class:`~streamparse.Spout` attributes.


Simple Python Example
^^^^^^^^^^^^^^^^^^^^^

The first step to putting together a topology, is creating the bolts and spouts,
so let's assume we have the following bolt and spout:

.. literalinclude:: ../../examples/redis/src/bolts.py
    :language: python
    :lines: 1-28

.. literalinclude:: ../../examples/redis/src/spouts.py
    :language: python

One important thing to note is that we have added an ``outputs`` attribute to
these classes, which specify the names of the output fields that will be
produced on their ``default`` streams.  If we wanted to specify multiple
streams, we could do that by specifying a list of :class:`~streamparse.Stream`
objects.

Now let's hook up the bolt to read from the spout:

.. literalinclude:: ../../examples/redis/topologies/wordcount_mem.py
    :language: python

.. note::
    Your project's ``src`` directory gets added to ``sys.path`` before your
    topology is imported, so you should use absolute imports based on that.

As you can see, :meth:`streamparse.Bolt.spec` and
:meth:`streamparse.Spout.spec` methods allow us to specify information about
the components in your topology and how they connect to each other.  Their
respective docstrings outline all of the possible ways they can be used.

Java Components
^^^^^^^^^^^^^^^

The topology DSL fully supports JVM-based bolts and spouts via the
:class:`~streamparse.JavaBolt` and :class:`~streamparse.JavaSpout` classes.

Here's an example of how we would use the
`Storm Kafka Spout <http://storm.apache.org/releases/current/storm-kafka.html>`_:

.. literalinclude:: ../../examples/kafka-jvm/topologies/pixelcount.py
    :language: python

One limitation of the Thrift interface we use to send the topology to Storm is
that the constructors for Java components can only be passed basic Python data
types: `bool`, `bytes`, `float`, `int`,  and `str`.

Components in Other Languages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have components that are written in languages other than Java or Python,
you can have those as part of your topology as well—assuming you're using the
corresponding multi-lang library for that language.

To do that you just need to use the :meth:`streamparse.ShellBolt.spec` and
:meth:`streamparse.ShellSpout.spec` methods.  They take ``command`` and
``script`` arguments to specify a binary to run and its string-separated
arguments.

Multiple Streams
^^^^^^^^^^^^^^^^

To specify that a component has multiple output streams, instead of using a
list of strings for :attr:`~streamparse.dsl.component.ComponentSpec.outputs`,
you must specify a list of :class:`~streamparse.Stream` objects, as shown below.

.. code-block:: python

    class FancySpout(Spout):
        outputs = [Stream(fields=['good_data'], name='default'),
                   Stream(fields=['bad_data'], name='errors')]

To select one of those streams as the input for a downstream
:class:`~streamparse.Bolt`, you simply use ``[]`` to specify the stream you
want. Without any stream specified, the ``default`` stream will be used.

.. code-block:: python

    class ExampleTopology(Topology):
        fancy_spout = FancySpout.spec()
        error_bolt = ErrorBolt.spec(inputs=[fancy_spout['errors']])
        process_bolt = ProcessBolt.spec(inputs=[fancy_spout])


Groupings
^^^^^^^^^

By default, Storm uses a :attr:`~streamparse.Grouping.SHUFFLE` grouping to route
tuples to particular executors for a given component, but you can also specify
other groupings by using the appropriate :class:`~streamparse.Grouping`
attribute. The most common grouping is probably the
:meth:`~streamparse.Grouping.fields` grouping, which will send all the tuples
with the same value for the specified fields to the same executor. This can be
seen in the prototypical word count topology:

.. literalinclude:: ../../examples/redis/topologies/wordcount_mem.py
    :language: python


Topology Cycles
^^^^^^^^^^^^^^^

On rare occasions, you may want to create a cyclical topology. This may not
seem easily done with the current topology DSL, but there is a workaround you
can use: manually declaring a temporary lower-level
`:class:~streamparse.thrift.GlobalStreamId` that you can refer to in multiple
places.

The following code creates a :class:`~streamparse.Topology` with a cycle
between its two Bolts.

.. code-block:: python

    from streamparse.thrift import GlobalStreamId

    # Create a reference to B's output stream before we even declare Topology
    b_stream = GlobalStreamId(componentId='b_bolt', streamId='default')

    class CyclicalTopology(Topology):
        some_spout = SomeSpout.spec()
        # Include our saved stream in your list of inputs for A
        a_bolt = A.spec(name="A", inputs=[some_spout, b_stream])
        # Have B get input from A like normal
        b_bolt = B.spec(name="B", inputs=[a_bolt])


Topology-Level Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to set a config option for all components in your topology, like
``topology.environment``, you can do that by adding a ``config`` class attribute
to your :class:`~streamparse.Topology` that is a `dict` mapping from option
names to their values.  For example:

.. code-block:: python

    class WordCount(Topology):
        config = {'topology.environment': {'LD_LIBRARY_PATH': '/usr/local/lib/'}}
        ...


Running Topologies
------------------

What Streamparse Does
^^^^^^^^^^^^^^^^^^^^^

When you run a topology either locally or by submitting to a cluster,
streamparse will

1. Bundle all of your code into a JAR
2. Build a Thrift Topology struct out of your Python topology definition.
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

Both ``sparse run`` and ``sparse submit`` accept a ``-p N`` command-line flag
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


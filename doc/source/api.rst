API
===


Tuples
------

.. autoclass:: streamparse.Tuple
    :no-members:
    :no-inherited-members:

You should never have to instantiate an instance of a
:class:`streamparse.Tuple` yourself as streamparse handles this for you
prior to, for example, a :class:`streamparse.Bolt`'s ``process()`` method
being called.

None of the emit methods for bolts or spouts require that you pass a
:class:`streamparse.Tuple` instance.


Components
----------

Both :class:`streamparse.Bolt` and :class:`streamparse.Spout` inherit from a
common base-class, :class:`streamparse.storm.component.Component`.  It extends
pystorm's code for handling `Multi-Lang IPC between Storm and Python <https://storm.apache.org/documentation/Multilang-protocol.html>`__
and adds suport for our Python :ref:`topology_dsl`.

Spouts
^^^^^^

Spouts are data sources for topologies, they can read from any data source and
emit tuples into streams.

.. autoclass:: streamparse.Spout
    :show-inheritance:

.. autoclass:: streamparse.ReliableSpout
    :show-inheritance:


Bolts
^^^^^

.. autoclass:: streamparse.Bolt
    :show-inheritance:

.. autoclass:: streamparse.BatchingBolt
    :show-inheritance:

.. autoclass:: streamparse.TicklessBatchingBolt
    :show-inheritance:


Logging
-------

.. autoclass:: streamparse.StormHandler
    :show-inheritance:
    :no-inherited-members:

Topology DSL
------------

.. autoclass:: streamparse.Topology
    :no-members:
    :no-inherited-members:

.. autoclass:: streamparse.Grouping

.. autoclass:: streamparse.Stream

.. autoclass:: streamparse.JavaBolt
    :members: spec
    :no-inherited-members:

.. autoclass:: streamparse.JavaSpout
    :members: spec
    :no-inherited-members:

.. autoclass:: streamparse.ShellBolt
    :members: spec
    :no-inherited-members:

.. autoclass:: streamparse.ShellSpout
    :members: spec
    :no-inherited-members:

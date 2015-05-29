API
===


Tuples
------

.. autoclass:: streamparse.storm.component.Tuple

You should never have to instantiate an instance of a
:class:`streamparse.storm.component.Tuple` yourself as streamparse handles this for you
prior to, for example, a :class:`streamparse.storm.bolt.Bolt`'s ``process()`` method
being called.

None of the emit methods for bolts or spouts require that you pass a
:class:`streamparse.storm.component.Tuple` instance.


Components
----------

Both :class:`streamparse.storm.bolt.Bolt` and
:class:`streamparse.storm.spout.Spout` inherit from a common base-class,
:class:`streamparse.storm.component.Component`.  It handles the basic
`Multi-Lang IPC between Storm and Python <https://storm.apache.org/documentation/Multilang-protocol.html>`__.

.. autoclass:: streamparse.storm.component.Component
    :inherited-members:

Spouts
^^^^^^

Spouts are data sources for topologies, they can read from any data source and
emit tuples into streams.

.. autoclass:: streamparse.storm.spout.Spout
    :inherited-members:
    :show-inheritance:

Bolts
^^^^^

.. autoclass:: streamparse.storm.bolt.Bolt
    :inherited-members:
    :show-inheritance:


.. autoclass:: streamparse.storm.bolt.BatchingBolt
    :inherited-members:
    :show-inheritance:

API
===


Tuples
------

.. autoclass:: pystorm.component.Tuple

You should never have to instantiate an instance of a
:class:`pystorm.component.Tuple` yourself as streamparse handles this for you
prior to, for example, a :class:`pystorm.bolt.Bolt`'s ``process()`` method
being called.

None of the emit methods for bolts or spouts require that you pass a
:class:`pystorm.component.Tuple` instance.


Components
----------

Both :class:`pystorm.bolt.Bolt` and :class:`pystorm.spout.Spout` inherit from a
common base-class, :class:`pystorm.component.Component`.  It handles the basic
`Multi-Lang IPC between Storm and Python
<https://storm.apache.org/documentation/Multilang-protocol.html>`__.

.. autoclass:: pystorm.component.Component
    :inherited-members:

Spouts
^^^^^^

Spouts are data sources for topologies, they can read from any data source and
emit tuples into streams.

.. autoclass:: pystorm.spout.Spout
    :inherited-members:
    :show-inheritance:

Bolts
^^^^^

.. autoclass:: pystorm.bolt.Bolt
    :inherited-members:
    :show-inheritance:


.. autoclass:: pystorm.bolt.BatchingBolt
    :inherited-members:
    :show-inheritance:

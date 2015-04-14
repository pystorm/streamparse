API
===


Tuples
------

.. autoclass:: streamparse.component.Tuple

You should never have to instantiate an instance of a
:class:`streamparse.component.Tuple` yourself as streamparse handles this for you
prior to, for example, a :class:`streamparse.bolt.Bolt`'s ``process()`` method
being called.

None of the emit methods for bolts or spouts require that you pass a
:class:`streamparse.component.Tuple` instance.


Spouts
------

Spouts are data sources for topologies, they can read from any data source and
emit tuples into streams.

.. autoclass:: streamparse.spout.Spout
    :members:


Bolts
-----

.. autoclass:: streamparse.bolt.Bolt
    :members:
    :show-inheritance:

.. autoclass:: streamparse.bolt.BatchingBolt
    :members:
    :show-inheritance:

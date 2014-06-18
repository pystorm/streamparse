API
===


Tuples
------

.. autoclass:: streamparse.ipc.Tuple

You should never have to instantiate an instance of a
:class:`streamparse.ipc.Tuple` yourself as streamparse handles this for you
prior to, for example, a :class:`streamparse.bolt.Bolt`'s ``process()`` method
being called.

None of the emit methods for bolts or spouts require that you pass a
:class:`streamparse.ipc.Tuple` instance.

Spouts
------

Spouts are data sources for topologies, they can read from any data source and
emit tuples into streams.

.. autoclass:: streamparse.spout.Spout
    :members: initialize, emit, emit_many, ack, fail, log, next_tuple


Bolts
-----

.. autoclass:: streamparse.bolt.Bolt
    :members: ack, emit, emit_many, fail, initialize, process, log
    :show-inheritance:

.. autoclass:: streamparse.bolt.BasicBolt
    :members:
    :show-inheritance:

.. autoclass:: streamparse.bolt.BatchingBolt
    :members: group_key, process_batch, SECS_BETWEEN_BATCHES
    :show-inheritance:

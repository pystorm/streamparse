API
===


Tuples
------

.. autoclass:: streamparse.ipc.Tuple


Spouts
------

Spouts are data sources for topologies, they can read from any data source and
emit tuples into streams.

.. autoclass:: streamparse.spout.Spout
    :members: initialize, emit, emit_many, ack, fail, log


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

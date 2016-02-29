.. versionadded:: 3.0

Topology DSL
============

To simplify the process of creating Storm topologies, streamparse features a
Python Topology `DSL <https://en.wikipedia.org/wiki/Domain-specific_language>`__.
It lets you specify topologies as complex as those you can in `Java <https://github.com/apache/storm/blob/07629c1f898ebb0cedcc19e15e4813692b6a9345/examples/storm-starter/src/jvm/org/apache/storm/starter/WordCountTopology.java>`__
or `Clojure <https://github.com/apache/storm/blob/07629c1f898ebb0cedcc19e15e4813692b6a9345/examples/storm-starter/src/clj/org/apache/storm/starter/clj/word_count.clj>`__,
but in concise, readable Python.


Topology
--------

.. autoclass:: streamparse.Topology

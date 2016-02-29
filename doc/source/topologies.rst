.. versionadded:: 3.0.0

Topology DSL
============

To simplify the process of creating Storm topologies, streamparse features a
Python Topology `DSL <https://en.wikipedia.org/wiki/Domain-specific_language>`__.
It lets you specify topologies as complex as those you can in `Java <https://github.com/apache/storm/blob/07629c1f898ebb0cedcc19e15e4813692b6a9345/examples/storm-starter/src/jvm/org/apache/storm/starter/WordCountTopology.java>`__
or `Clojure <https://github.com/apache/storm/blob/07629c1f898ebb0cedcc19e15e4813692b6a9345/examples/storm-starter/src/clj/org/apache/storm/starter/clj/word_count.clj>`__,
but in concise, readable Python.

Creating a Topology in Python
-----------------------------

1.  Create a Python module with the name of your topology (e.g., ``wordcount.py``) inside your projects ``topologies`` directory.
2.	Add a class that inherits from :class:`streamparse.Topology` to your file that specifies the bolts and spouts in your topology and their connections.

  	.. literalinclude:: ../../examples/redis/topologies/wordcount_mem.py
  		:language: python



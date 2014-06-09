Quickstart
==========

Dependencies
------------

Java and Clojure
^^^^^^^^^^^^^^^^

To run local and remote computation clusters, streamparse relies upon a JVM
technology called Apache Storm. The integration with this technology is
lightweight, and for the most part, you don't need to think about it.

However, to get the library running, you'll need

1. JDK 7+, which you can install with apt-get, homebrew, or an installler;
   and
2. lein, which you can install from the
   `project's page <http://leiningen.org/>`_ or
   `github <https://github.com/technomancy/leiningen#leiningen>`_

Confirm that you have ``lein`` installed by running::

    > lein version

You should get output similar to this::

    Leiningen 2.3.4 on Java 1.7.0_55 Java HotSpot(TM) 64-Bit Server VM

If ``lein`` isn't installed,
`follow these directions <leiningen.org/#install>`_.

Once that's all set, you install streamparse using ``pip``::

    > pip install streamparse


Your First Project
------------------

When working with streamparse, your first step is to create a project using
the command-line tool, ``sparse``::

    > sparse quickstart wordcount

    Creating your wordcount streamparse project...
        create    wordcount
        create    wordcount/.gitignore
        create    wordcount/config.json
        create    wordcount/fabfile.py
        create    wordcount/project.clj
        create    wordcount/README.md
        create    wordcount/src
        create    wordcount/src/wordcount.py
        create    wordcount/src/words.py
        create    wordcount/tasks.py
        create    wordcount/topologies
        create    wordcount/topologies/wordcount.clj
        create    wordcount/virtualenvs
        create    wordcount/virtualenvs/wordcount.txt
    Done.

    Try running your topology locally with:

        cd wordcount
        sparse run

The quickstart project provides a basic wordcount topology example which you
can examine and modify. You can inspect the other commands that ``sparse``
provides by running::

    > sparse -h


Project Structure
-----------------

streamparse projects expect to have the following directory layout:

.. csv-table::
    :header: "File/Folder","Contents"
    :widths: 30,70

    "config.json","Configuration information for all of your topologies."
    "fabfile.py","Optional custom fabric tasks."
    "project.clj","leiningen project file."
    "src/","Python source files (bolts/spouts/etc.) for topologies."
    "tasks.py","Optional custom invoke tasks."
    "topologies/","Contains topology definitions written using the `Clojure DSL <http://storm.incubator.apache.org/documentation/Clojure-DSL.html>`_ for Storm."
    "virtualenvs/","Contains pip requirements files in order to install dependencies on remote Storm servers."


Defining Topologies
-------------------

Storm's services are Thrift-based and although it is possible to define a
topology in pure Python using Thrift, it introduces a host of additional
dependencies which are less than ideal for local development. In addition, it
turns out that using Clojure to define topologies, still feels fairly Pythonic.

Let's have a look at the definition file created by using the
``sparse quickstart`` command.

.. code-block:: clojure

    (ns wordcount
      (:use     [backtype.storm.clojure])
      (:gen-class))

    (def wordcount
       [
        ;; spout configuration
        {"word-spout" (shell-spout-spec
              ["python" "words.py"]
              ["word"]
              )
        }
        ;; bolt configuration
        {"count-bolt" (shell-bolt-spec
               {"word-spout" :shuffle}
               ["python" "wordcount.py"]
               ["word" "count"]
               :p 2
               )
        }
      ]
    )

The first block of code we encounter effectively states "import the
Clojure-DSL functions for Storm":

.. code-block:: clojure

    (ns wordcount
      (:use     [backtype.storm.clojure])
      (:gen-class))

The next block of code actually defines the topology and stores it into a var
named "topology".

.. code-block:: clojure

    (def wordcount
       [
        ;; spout configuration
        {"word-spout" (shell-spout-spec
              ["python" "words.py"]
              ["word"]
              )
        }
        ;; bolt configuration
        {"count-bolt" (shell-bolt-spec
               {"word-spout" :shuffle}
               ["python" "wordcount.py"]
               ["word" "count"]
               :p 2
               )
        }
      ]
    )

It turns out, the name of the name of the var doesn't matter much, we've used
"wordcount" above, but it could just as easily be "topology".

This variable holds an array with only two dictionaries.  The first dictionary
holds a named mapping of all the spouts that exist in the topology whereas the
second dictionary holds a named mapping of all the bolts that exist in the
topologies.

TODO: Finish this section.


Spouts and Bolts
----------------

TODO: Finish this section.

Remote Deployment
-----------------

TODO: Finish this section.

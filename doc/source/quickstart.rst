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
    "project.clj","leiningen project file, can be used to add external JVM dependencies."
    "src/","Python source files (bolts/spouts/etc.) for topologies."
    "tasks.py","Optional custom invoke tasks."
    "topologies/","Contains topology definitions written using the `Clojure DSL <http://storm.incubator.apache.org/documentation/Clojure-DSL.html>`_ for Storm."
    "virtualenvs/","Contains pip requirements files in order to install dependencies on remote Storm servers."


Defining Topologies
-------------------

Storm's services are Thrift-based and although it is possible to define a
topology in pure Python using Thrift, it introduces a host of additional
dependencies which are less than trivial to setup for local development. In
addition, it turns out that using Clojure to define topologies, still feels
fairly Pythonic, so the authors of streamparse decided this was a good
compromise.

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
Clojure DSL functions for Storm":

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
``wordcount`` above, but it could just as easily be ``bananas``. What is
important, is that **the var must be an array with only two dictionaries**.

The first dictionary holds a named mapping of all the spouts that exist in the
topology, the second holds a named mapping of all the bolts. An additional
benefit of definint topologies in Clojure is that we're able to mix and match
the types of spouts and bolts.  In most cases, you may want to use a pure
Python topology, but you could easily use JVM-based spouts and bolts or even
spouts and bolts written in other languages like Ruby, Go, etc.

Since you'll most often define spouts and bolts in Python however, we'll look
at the two most important functions exposed by the Clojure DSL
``shell-spout-spec`` and ``shell-bolt-spec``.

When creating a Python-based spout, we provide a name for the spout and a
definition of that spout via ``shell-spout-spec``:

.. code-block:: clojure

    {"sentence-spout-1" (shell-spout-spec
                         ;; the command to run, can be any executable
                         ["python" "sentence.py"]
                         ;; output specification, what named fields will this spout emit?
                         ["sentence"]
                         ;; configuration parameters, can specify multiple
                         :p 2)
     "sentence-spout-2" (shell-spout-spec
                         ["python" "other_sentence_spout.py"]
                         ["sentence"])}

In the example above, we've defined two spouts in our topology:
``word-spout-1`` and ``word-spout-2`` and told Storm to run these components
using the ``python`` commmand with the appropriate script in relative to our
``src`` directory.  We've also let Storm know exactly what these spouts will be
emitting, namely a single field called ``word``.

You'll notice that in ``word-spout-1``, we've passed an optional map of
configuraiton parameters ``:p 2``, we'll get back to this later.

Creating bolts is very similar and uses the ``shell-bolt-spec`` function:

.. code-block:: clojure

    {"sentence-splitter" (shell-bolt-spec
                          ;; inputs, where does this bolt recieve it's tuples from?
                          {"word-spout-1" :shuffle
                           "word-spout-2" :shuffle}
                          ;; command to run
                          ["python" "sentence_splitter.py"]
                          ;; output spec, what tuples does this bolt emit?
                          ["word"]
                          ;; configuration parameters
                          :p 2)
     "word-counter" (shell-bolt-spec
                     ;; recieves tuples from "sentence-splitter", grouped by word
                     {"sentence-splitter" ["word"]}
                     ["python" "word_counter.py"]
                     ["word" "count"])
     "word-count-saver" (shell-bolt-spec
                         {"word-counter" :shuffle}
                         ["python" "word_saver.py"]
                         ;; does not emit any fields
                         [])}

In the example above, we define 3 bolts by name ``sentence-splitter``,
``word-counter`` and ``word-count-saver``. Since bolts are generally supposed
to process some input and optionally produce some output, we have to tell Storm
where a bolts inputs come from and whether or not we'd like Storm to use any
stream grouping on the tuples from the input source.

In the ``sentence-splitter`` bolt, you'll notice that we define two input
sources for the bolt, completely fine to add multiple sources to any bolts.

In the ``word-counter`` bolt, we've told Storm that we'd like the stream of
input tuples to be grouped by the named field ``word``. Storm offers
comprehensive options for `stream groupings
<http://storm.incubator.apache.org/documentation/Concepts.html#stream-groupings>`_,
but you will most commonly use a **shuffle** or **fields** grouping:

* **Shuffle grouping**: Tuples are randomly distributed across the bolt’s tasks
  in a way such that each bolt is guaranteed to get an equal number of tuples.
* **Fields grouping**: The stream is partitioned by the fields specified in the
  grouping. For example, if the stream is grouped by the “user-id” field,
  tuples with the same “user-id” will always go to the same task, but tuples
  with different “user-id”’s may go to different tasks.

There are more options to configure with spouts and bolts, we'd encourage you
to refer to `Storm's Concepts
<http://storm.incubator.apache.org/documentation/Concepts.html>`_ for more
information.

Spouts and Bolts
----------------

The general flow for creating new spouts and bolts using streamparse is to add
them to your ``src`` folder and update the corresponding topology definition.

Let's create a spout that emits sentences until the end of time:

.. code-block:: python

    import itertools

    from streamparse.spout import Spout


    class SentenceSpout(Spout):

        def initialize(self, stormconf, context):
            self.sentences = [
                "She advised him to take a long holiday, so he immediately quit work and took a trip around the world",
                "I was very glad to get a present from her",
                "He will be here in half an hour",
                "She saw him eating a sandwich",
            ]
            self.sentences = itertools.cycle(self.sentences)

        def next_tuple(self):
            sentence = next(self.sentences)
            self.emit([sentence])

        def ack(self, tup_id):
            pass  # if a tuple is processed properly, do nothing

        def fail(self, tup_id):
            pass  # if a tuple fails to process, do nothing


    if __name__ == '__main__':
        SentenceSpout().run()

The magic in the code above happens in the ``initialize()`` and
``next_tuple()`` functions.  Once the spout enters the main run loop (via the
``run()`` method), streamparse will call your spout's ``initialize()`` method.
After initialization is complete, streamparse will continually call the spout's
``next_tuple()`` method where you're expected to emit tuples that match
whatever you've defined in your topology definition.

Now let's create a bolt that takes in sentences, and spits out words:

.. code-block:: python

    import re

    from streamparse.bolt import Bolt

    class SentenceSplitterBolt(Bolt):

        def process(self, tup):
            sentence = tup.values[0]  # extract the sentence
            sentence = re.sub(r"[,.;!\?]", "", sentence)  # get rid of punctuation
            words = [[word.strip()] for word in sentence.split(" ") if word.strip()]
            if not words:
                # no words to process in the sentence, fail the tuple
                self.fail(tup)
                return

            self.emit_many(words)
            self.ack(tup)  # tell Storm the tuple has been processed successfully

    if __name__ == '__main__':
        SentenceSplitterBolt().run()

The bolt implementation is even simpler. We simply override the default
``process()`` method which streamparse calls when a tuple has been emitted by
an incoming spout or bolt. You are welcome to do whatever processing you would
like in this method and can further emit tuples or not depending on the purpose
of your bolt.

In the ``SentenceSplitterBolt`` above, we have decided to use the
``emit_many()`` method instead of ``emit()`` which is a bit more efficient when
sending a larger number of tuples to Storm.

After processing of the tuple is complete, we tell Storm the tuple was
successfully processed by calling the bolt's ``ack()`` method and passing the
input tuple we received.  If you're writing simple bolt that should always call
``ack()`` after processing completes, you can use the
:class:`streamparse.bolt.BasicBolt` class.

Failed Tuples
^^^^^^^^^^^^^

In the example above, we added the ability to fail a sentence tuple if it
did not provide any words. What happens when we fail a tuple? Storm will send a
"fail" message back to the spout where the tuple originated from (in this case
``SentenceSpout``) and streamparse calls the spout's ``fail()`` method. It's
then up to your spout implementation to decide what to do. A spout could retry
a failed tuple, send an error message, or kill the topology.

Remote Deployment
-----------------

When you are satisfied that your topology works well via testing with::

    > sparse run -d

You can submit your topology to a remote Storm cluster using the command::

    sparse submit [--environment <env>] [--name <topology>] [-dv]

Before submitting, you have to have at least one environment configured in your
project's ``config.json`` file. Let's create a sample environment called "prod"
in our ``config.json`` file:

.. code-block:: json

    {
        "library": "",
        "topology_specs": "topologies/",
        "virtualenv_specs": "virtualenvs/",
        "envs": {
            "prod": {
                "user": "storm",
                "nimbus": "storm1.my-cluster.com",
                "workers": [
                    "storm1.my-cluster.com",
                    "storm2.my-cluster.com",
                    "storm3.my-cluster.com"
                ],
                "log_path": "",
                "virtualenv_root": "/data/virtualenvs/"
            }
        }
    }

We've now defined a ``prod`` environment that will use the user ``storm`` when
deploying topologies. Before submitting the topology though, streamparse will
automatically take care of instaling all the dependencies your topology
requires. It does this by sshing into everyone of the nodes in the ``workers``
config variable and building a virtualenv using the the project's local
``virtualenvs/<topology_name>.txt`` requirements file.

This implies a few requirements about the user you specify per environment:

1. Must have ssh access to all servers in your Storm cluster
2. Must have write access to the ``virtualenv_root`` on all servers in your
   Storm cluster

streamparse also assumes that virtualenv is installed on all Storm servers.

Once an environment is configured, we could deploy our wordcount topology like
so::

    > sparse submit

Seeing as we have only one topology and environment, we don't need to specify
these explicitly. streamparse will now:

1. Package up a JAR containing all your Python source files
2. Build a virtualenv on all your Storm workers (in parallel)
3. Submit the topology to the ``nimbus`` server

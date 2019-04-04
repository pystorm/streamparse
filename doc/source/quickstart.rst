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
   `Leiningen project page <http://leiningen.org/>`_ or
   `github <https://github.com/technomancy/leiningen#leiningen>`_
3. Apache Storm development environment, which you can install from the
   `Storm project page <http://storm.apache.org/releases/current/Setting-up-development-environment.html>`_

   You will need to have at least Apache Storm version 0.10.0 to cooperate with Streamparse.

Confirm that you have ``lein`` installed by running::

    > lein version

You should get output similar to this::

     Leiningen 2.3.4 on Java 1.7.0_55 Java HotSpot(TM) 64-Bit Server VM

Confirm that you have ``storm`` installed by running::

    > storm version

You should get output similar to this::

    Running: java -client -Ddaemon.name= -Dstorm.options= -Dstorm.home=/opt/apache-storm-1.0.1 -Dstorm.log.dir=/opt/apache-storm-1.0.1/logs -Djava.library.path=/usr/local/lib:/opt/local/lib:/usr/lib -Dstorm.conf.file= -cp /opt/apache-storm-1.0.1/lib/reflectasm-1.10.1.jar:/opt/apache-storm-1.0.1/lib/kryo-3.0.3.jar:/opt/apache-storm-1.0.1/lib/log4j-over-slf4j-1.6.6.jar:/opt/apache-storm-1.0.1/lib/clojure-1.7.0.jar:/opt/apache-storm-1.0.1/lib/log4j-slf4j-impl-2.1.jar:/opt/apache-storm-1.0.1/lib/servlet-api-2.5.jar:/opt/apache-storm-1.0.1/lib/disruptor-3.3.2.jar:/opt/apache-storm-1.0.1/lib/objenesis-2.1.jar:/opt/apache-storm-1.0.1/lib/storm-core-1.0.1.jar:/opt/apache-storm-1.0.1/lib/slf4j-api-1.7.7.jar:/opt/apache-storm-1.0.1/lib/storm-rename-hack-1.0.1.jar:/opt/apache-storm-1.0.1/lib/log4j-api-2.1.jar:/opt/apache-storm-1.0.1/lib/log4j-core-2.1.jar:/opt/apache-storm-1.0.1/lib/minlog-1.3.0.jar:/opt/apache-storm-1.0.1/lib/asm-5.0.3.jar:/opt/apache-storm-1.0.1/conf org.apache.storm.utils.VersionInfo
    Storm 1.0.1
    URL https://git-wip-us.apache.org/repos/asf/storm.git -r b5c16f919ad4099e6fb25f1095c9af8b64ac9f91
    Branch (no branch)
    Compiled by tgoetz on 2016-04-29T20:44Z
    From source with checksum 1aea9df01b9181773125826339b9587e


If ``lein`` isn't installed,
 `follow these directions to install it <http://leiningen.org/#install>`_.

If ``storm`` isn't installed,
`follow these directions <http://storm.apache.org/releases/current/Setting-up-development-environment.html>`_.

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
        create    wordcount/src/bolts/
        create    wordcount/src/bolts/__init__.py
        create    wordcount/src/bolts/wordcount.py
        create    wordcount/src/spouts/
        create    wordcount/src/spouts/__init__.py
        create    wordcount/src/spouts/words.py
        create    wordcount/topologies
        create    wordcount/topologies/wordcount.py
        create    wordcount/virtualenvs
        create    wordcount/virtualenvs/wordcount.txt
    Done.

Try running your topology locally with::

    > cd wordcount
      sparse run

The quickstart project provides a basic wordcount topology example which you
can examine and modify. You can inspect the other commands that ``sparse``
provides by running::

    > sparse -h

If you see an error like::

    Local Storm version, 1.0.1, is not the same as the version in your project.clj, 0.10.0. The versions must match.

You will have to edit your wordcount/project.clj file and change Apache Storm library version to match the one you have installed.

Project Structure
-----------------

streamparse projects expect to have the following directory layout:

.. table::

    +----------------+---------------------------------------------------------------------------------------+
    | File/Folder    | Contents                                                                              |
    +================+=======================================================================================+
    | `config.json`  | Configuration information for all of your topologies.                                 |
    +----------------+---------------------------------------------------------------------------------------+
    | `fabfile.py`   | Optional custom fabric tasks.                                                         |
    +----------------+---------------------------------------------------------------------------------------+
    | `project.clj`  | leiningen project file (can be used to add external JVM dependencies).                |
    +----------------+---------------------------------------------------------------------------------------+
    | `src/`         | Python source files (bolts/spouts/etc.) for topologies.                               |
    +----------------+---------------------------------------------------------------------------------------+
    | `tasks.py`     | Optional custom invoke tasks.                                                         |
    +----------------+---------------------------------------------------------------------------------------+
    | `topologies/`  | Contains topology definitions written using the :ref:`topology_dsl`.                  |
    +----------------+---------------------------------------------------------------------------------------+
    | `virtualenvs/` | Contains pip requirements files used to install dependencies on remote Storm servers. |
    +----------------+---------------------------------------------------------------------------------------+

Defining Topologies
-------------------

Storm's services are Thrift-based and although it is possible to define a
topology in pure Python using Thrift.  For details see :ref:`topology_dsl`.

Let's have a look at the definition file created by using the
``sparse quickstart`` command.

.. literalinclude:: ../../streamparse/bootstrap/project/topologies/wordcount.py
    :language: python

In the ``count_bolt`` bolt, we've told Storm that we'd like the stream of
input tuples to be grouped by the named field ``word``. Storm offers
comprehensive options for
`stream groupings <http://storm.apache.org/documentation/Concepts.html#stream-groupings>`_,
but you will most commonly use a **shuffle** or **fields** grouping:

* **Shuffle grouping**: Tuples are randomly distributed across the bolt’s tasks
  in a way such that each bolt is guaranteed to get an equal number of tuples.
  This is the default grouping if no other is specified.
* **Fields grouping**: The stream is partitioned by the fields specified in the
  grouping. For example, if the stream is grouped by the "user-id" field,
  tuples with the same "user-id" will always go to the same task, but tuples
  with different "user-id"’s may go to different tasks.

There are more options to configure with spouts and bolts, we'd encourage you
to refer to our :ref:`topology_dsl` docs or
`Storm's Concepts <http://storm.apache.org/documentation/Concepts.html>`_ for
more information.

Spouts and Bolts
----------------

The general flow for creating new spouts and bolts using streamparse is to add
them to your ``src`` folder and update the corresponding topology definition.

Let's create a spout that emits sentences until the end of time:

.. code-block:: python

    import itertools

    from streamparse.spout import Spout


    class SentenceSpout(Spout):
        outputs = ['sentence']

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

The magic in the code above happens in the ``initialize()`` and
``next_tuple()`` functions.  Once the spout enters the main run loop,
streamparse will call your spout's ``initialize()`` method.
After initialization is complete, streamparse will continually call the spout's
``next_tuple()`` method where you're expected to emit tuples that match
whatever you've defined in your topology definition.

Now let's create a bolt that takes in sentences, and spits out words:

.. code-block:: python

    import re

    from streamparse.bolt import Bolt

    class SentenceSplitterBolt(Bolt):
        outputs = ['word']

        def process(self, tup):
            sentence = tup.values[0]  # extract the sentence
            sentence = re.sub(r"[,.;!\?]", "", sentence)  # get rid of punctuation
            words = [[word.strip()] for word in sentence.split(" ") if word.strip()]
            if not words:
                # no words to process in the sentence, fail the tuple
                self.fail(tup)
                return

            for word in words:
                self.emit([word])
            # tuple acknowledgement is handled automatically

The bolt implementation is even simpler. We simply override the default
``process()`` method which streamparse calls when a tuple has been emitted by
an incoming spout or bolt. You are welcome to do whatever processing you would
like in this method and can further emit tuples or not depending on the purpose
of your bolt.

If your ``process()`` method completes without raising an Exception, streamparse
will automatically ensure any emits you have are anchored to the current tuple
being processed and acknowledged after ``process()`` completes.

If an Exception is raised while ``process()`` is called, streamparse
automatically fails the current tuple prior to killing the Python process.

Failed Tuples
^^^^^^^^^^^^^

In the example above, we added the ability to fail a sentence tuple if it did
not provide any words. What happens when we fail a tuple? Storm will send a
"fail" message back to the spout where the tuple originated from (in this case
``SentenceSpout``) and streamparse calls the spout's
:meth:`~streamparse.storm.spout.Spout.fail` method. It's then up to your spout
implementation to decide what to do. A spout could retry a failed tuple, send
an error message, or kill the topology. See :ref:`dealing-with-errors` for
more discussion.

Bolt Configuration Options
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can disable the automatic acknowleding, anchoring or failing of tuples by
adding class variables set to false for: ``auto_ack``, ``auto_anchor`` or
``auto_fail``.  All three options are documented in
:class:`streamparse.bolt.Bolt`.

**Example**:

.. code-block:: python

    from streamparse.bolt import Bolt

    class MyBolt(Bolt):

        auto_ack = False
        auto_fail = False

        def process(self, tup):
            # do stuff...
            if error:
              self.fail(tup)  # perform failure manually
            self.ack(tup)  # perform acknowledgement manually

Handling Tick Tuples
^^^^^^^^^^^^^^^^^^^^

Ticks tuples are built into Storm to provide some simple forms of
cron-like behaviour without actually having to use cron. You can
receive and react to tick tuples as timer events with your python
bolts using streamparse too.

The first step is to override ``process_tick()`` in your custom
Bolt class. Once this is overridden, you can set the storm option
``topology.tick.tuple.freq.secs=<frequency>`` to cause a tick tuple
to be emitted every ``<frequency>`` seconds.

You can see the full docs for ``process_tick()`` in
:class:`streamparse.bolt.Bolt`.

**Example**:

.. code-block:: python

    from streamparse.bolt import Bolt

    class MyBolt(Bolt):

        def process_tick(self, freq):
            # An action we want to perform at some regular interval...
            self.flush_old_state()

Then, for example, to cause ``process_tick()`` to be called every
2 seconds on all of your bolts that override it, you can launch
your topology under ``sparse run`` by setting the appropriate -o
option and value as in the following example:

.. code-block:: bash

    $ sparse run -o "topology.tick.tuple.freq.secs=2" ...

.. _remote_deployment:

Remote Deployment
-----------------

Setting up a Storm Cluster
^^^^^^^^^^^^^^^^^^^^^^^^^^

See Storm's `Setting up a Storm Cluster <https://storm.apache.org/documentation/Setting-up-a-Storm-cluster.html>`_.

Submit
^^^^^^

When you are satisfied that your topology works well via testing with::

    > sparse run -d

You can submit your topology to a remote Storm cluster using the command::

    sparse submit [--environment <env>] [--name <topology>] [-dv]

Before submitting, you have to have at least one environment configured in your
project's ``config.json`` file. Let's create a sample environment called "prod"
in our ``config.json`` file:

.. code-block:: json

    {
        "serializer": "json",
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
                "log": {
                    "path": "/var/log/storm/streamparse",
                    "file": "pystorm_{topology_name}_{component_name}_{task_id}_{pid}.log",
                    "max_bytes": 100000,
                    "backup_count": 10,
                    "level": "info"
                },
                "use_ssh_for_nimbus": true,
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

If you would like to use your system user for creating the SSH connection to
the Storm cluster, you can omit the ``user`` setting from your ``config.json``.

By default the ``root`` user is used for creating virtualenvs when you do not
specify a ``user`` in your ``config.json``. To override this, set the
``sudo_user`` option in your ``config.json``. ``sudo_user`` will default to
``user`` if one is specified.

streamparse also assumes that virtualenv is installed on all Storm servers.

Once an environment is configured, we could deploy our wordcount topology like
so::

    > sparse submit

Seeing as we have only one topology and environment, we don't need to specify
these explicitly. streamparse will now:

1. Package up a JAR containing all your Python source files
2. Build a virtualenv on all your Storm workers (in parallel)
3. Submit the topology to the ``nimbus`` server

Disabling & Configuring Virtualenv Creation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you do not have ssh access to all of the servers in your Storm cluster, but
you know they have all of the requirements for your Python code installed, you
can set ``"use_virtualenv"`` to ``false`` in ``config.json``.

If you have virtualenvs on your machines that you would like streamparse to
use, but not update or manage, you can set ``"install_virtualenv"`` to ``false``
in ``config.json``.

If you would like to pass command-line flags to virtualenv, you can set
``"virtualenv_flags"`` in ``config.json``, for example::

    "virtualenv_flags": "-p /path/to/python"

Note that this only applies when the virtualenv is created, not when an
existing virtualenv is used.

If you would like to share a single virtualenv across topologies, you can set
``"virtualenv_name"`` in ``config.json`` which overrides the default behaviour
of using the topology name for virtualenv. Updates to a shared virtualenv should
be done after shutting down topologies, as code changes in running topologies
may cause errors.

Using unofficial versions of Storm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you wish to use streamparse with unofficial versions of storm (such as the HDP Storm)
you should set ``:repositories`` in your ``project.clj`` to point to the Maven repository
containing the JAR you want to use, and set the version in ``:dependencies`` to match
the desired version of Storm.

For example, to use the version supplied by HDP, you would set ``:repositories`` to:

``:repositories {"HDP Releases" "http://repo.hortonworks.com/content/repositories/releases"}``

Local Clusters
^^^^^^^^^^^^^^

Streamparse assumes that your Storm cluster is not on your local machine. If it
is, such as the case with VMs or Docker images, change ``"use_ssh_for_nimbus"``
in ``config.json`` to ``false``.


Setting Submit Options in config.json
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you frequently use the same options to ``sparse submit`` in your project, you
can set them in ``config.json`` using the ``options`` key in your environment
settings.  For example:

.. code-block:: json

    {
        "topology_specs": "topologies/",
        "virtualenv_specs": "virtualenvs/",
        "envs": {
            "vagrant": {
                "user": "vagrant",
                "nimbus": "streamparse-box",
                "workers": [
                    "streamparse-box"
                ],
                "virtualenv_root": "/data/virtualenvs",
                "options": {
                    "topology.environment": {
                        "LD_LIBRARY_PATH": "/usr/local/lib/"
                    }
                }
            }
        }
    }

You can also set the ``--worker`` and ``--acker`` parameters in ``config.json``
via the ``worker_count`` and ``acker_count`` keys in your environment settings.

.. code-block:: json

    {
        "topology_specs": "topologies/",
        "virtualenv_specs": "virtualenvs/",
        "envs": {
            "vagrant": {
                "user": "vagrant",
                "nimbus": "streamparse-box",
                "workers": [
                    "streamparse-box"
                ],
                "virtualenv_root": "/data/virtualenvs",
                "acker_count": 1,
                "worker_count": 1
            }
        }
    }


Logging
^^^^^^^

The Storm supervisor needs to have access to the ``log.path`` directory for
logging to work (in the example above, ``/var/log/storm/streamparse``). If you
have properly configured the ``log.path`` option in your config, streamparse
will use the value for the ``log.file`` option to set up log files for each
Storm worker in this path. The filename can be customized further by using
certain named placeholders. The default filename is set to::

    pystorm_{topology_name}_{component_name}_{task_id}_{pid}.log

Where:

* ``topology_name``: is the ``topology.name`` variable set in Storm
* ``component_name``: is the name of the currently executing component as defined in your topology definition file (.clj file)
* ``task_id``: is the task ID running this component in the topology
* ``pid``: is the process ID of the Python process

streamparse uses Python's ``logging.handlers.RotatingFileHandler`` and by
default will only save 10 1 MB log files (10 MB in total), but this can be
tuned with the ``log.max_bytes`` and ``log.backup_count`` variables.

The default logging level is set to ``INFO``, but if you can tune this with the
``log.level`` setting which can be one of critical, error, warning, info or
debug.  **Note** that if you perform ``sparse run`` or ``sparse submit`` with
the ``--debug`` set, this will override your ``log.level`` setting and set the
log level to debug.

When running your topology locally via ``sparse run``, your log path will be
automatically set to ``/path/to/your/streamparse/project/logs``.

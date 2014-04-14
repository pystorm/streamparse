# stormpy

stormpy is a Pythonic interop library for the Apache Storm framework.

## What is Storm and why should a Pythonista care about it?

Storm is a distributed real-time computation framework. Storm is sometimes
referred to as a "real-time map/reduce implementation". It allows you to define
computation as a directed acyclic graph (DAG) of processing nodes, called
Bolts. Bolts take a stream of named tuples as input. They produce one or more
streams of named tuples as output. Dependencies between Bolts are explicitly
declared. Data originates in a cluster via Spout, which simply exposes a stream
of named tuples. A Spout receives its source data from a high-performance queue
like Apache Kafka (though ZeroMQ, RabbitMQ, and other sources are also
options).

In short, the Spout and Bolts abstraction allows you to write Python code which
transforms a live stream of data and execute it performantly across a cluster
of machines. You can parallelize each step of your computation automatically,
and you can resize your cluster dynamically to add more processing power. Storm
also provides mechanisms to guarantee fault-tolerance and at-least-once message
processing semantics. It is a strong alternative to Celery for log and stream
processing problems.

## stormpy, Clojure, and lein

stormpy allows you to write your Storm Spout and Bolt implementations in pure
Python. It also provides mechanisms for managing and debugging your clusters.
But Storm is actually a language-independent technology. It is written in Java
and Clojure and runs on the JVM, but works with other programming languages via
its "multi-lang protocol". As a result of this flexibility, stormpy leverages
Storm's existing Clojure DSL for configuring Storm topologies. This allows you
to freely mix Python Spouts and Bolts with Java/Clojure Spouts and Bolts (as
well as Spouts and Bolts written in other languages altogether). This is
important because the community around Storm has written many re-usable
components in Java/Clojure. For example, there are several data integration
Spouts already written for tools like Kafka, RabbitMQ, ZeroMQ, MongoDB and
Cassandra. Therefore, every stormpy project is actually a mixed Python and
Clojure project.

The ``lein`` build tool is used to resolve dependencies to Storm itself,
install it locally, run Storm topologies locally, add dependencies for
community-supported JVM-based Spout implementations, offer an interactive
debugging REPL, and to package your topologies as an "uberjar" for submission
to a production Storm cluster.

You may be worried that this means to use stormpy, you need to know Clojure.
This is not the case. The Clojure DSL is essentially just a lightweight
configuration file format that happens to be written in Clojure. It isn't any
harder than JSON since it's ultimately just configured using some data maps.
Plus, we have plenty of examples for you to follow. And, we've provided a
simple tool for introspecting your Python Spouts and Bolts and offering
starting points for configuration.

## Core focus of this library

With Storm local building and packaging handled by ``lein``, this library has a
reduced scope and will only focus on a few key areas core to writing, running,
monitoring, and debugging Storm topologies in Python. These are:

* an enhanced Pythonic support library
* decorators for your Bolts and Spouts, ``@bolt`` and ``@spout``
* Python dependency management, utilizing virtualenv tooling
* logging and log tailing using the ``logging`` module and ``fabric``
* remote debugging that exposes ``pdb`` on each spout/bolt over a socket
* post-mortem debugging support that saves stack trace objects for ``pdb.pm()``
* out-of-box Sentry/Raven support
* local execution using Storm ``LocalCluster``

## Dependencies

### Java/Clojure

* JDK 1.7+
* lein

### Python

* fabric
* invoke

# Getting started

## Installation

After installing the Java requirements, you can run:

    pip install stormpy

This will offer a command-line tool, ``stormpy``. Use:

    stormpy quickstart

To create a project template which will have:

* src/
    * wordlib.py: example support library in Python
    * wordcount.py: example Spout & Bolt implementation in Python
* topologies/
    * wordcount.clj: ``clj`` file with topology configuration in Clojure DSL
* virtualenvs/
    * wordcount.txt: ``requirements`` file to express Python dependencies
* config.json: config file w/ Storm cluster hostnames and code locations
* project.clj: ``lein`` project file to express Storm dependencies
* fabfile.py: remote management tasks (fabric, customizable)
* tasks.py: local management tasks (invoke, customizable)

## Running and Debugging locally

You can then run the local Storm topology using:

    stormpy run-local

This will produce a lot of output and may also download Storm dependencies upon
first run.

You can debug a local Storm topology's Spout by running:

    stormpy debug-local --spout=wordcount.sample_spout

This will set a breakpoint when the Spout receives its first data tuple and let you trace through it.

You can debug a local Storm topology's Bolt by running:

    stormpy debug-local --bolt=wordcount.sample_bolt

This will set a breakpoint when the Bolt receives its first data tuple.

In both cases, debug-local uses ``pdb`` over a socket connection.

## Packaging and submitting

To package your uberjar for submission to a Storm cluster, use:

    stormpy package topologies/topology.clj

This will create a project JAR file containing all your Python code inside
``_target/``. Temporary build artifacts are stored in ``_build/``.

To submit your Storm topology to a locally-running Storm cluster, use:

    stormpy submit topologies/topology.clj

To submit your Storm topology to a remotely-running production Storm cluster, use:

    stormpy submit topologies/topology.clj --env=prod

The submit task will automatically package your topology before submitting.

## Monitoring

To monitor a running Storm topology in production, use:

    stormpy monitor --env=prod

To tail all the log files for a running topology across a production Storm
cluster, use:

    stormpy tail --env=prod

## Managing

To kill a running Storm topology, use:

    stormpy kill --env=prod

Topologies are automatically killed when you re-submit an existing topology to
a cluster.

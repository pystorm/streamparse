Frequently Asked Questions (FAQ)
================================

General Questions
-----------------

* `Why use streamparse?`_
* `Is streamparse compatible with Python 3?`_
* `How can I contribute to streamparse?`_
* `How do I trigger some code before or after I submit my topology?`_
* `How should I install streamparse on the cluster nodes?`_
* `Should I install Clojure?`_
* `How do I deploy into a VPC?`_
* `How do I override SSH settings?`_
* `How do I dynamically generate the worker list?`_


Why use streamparse?
~~~~~~~~~~~~~~~~~~~~

To lay your Python code out in topologies which can be automatically
parallelized in a Storm cluster of machines. This lets you scale your
computation horizontally and avoid issues related to Python's GIL. See
:ref:`parallelism`.

Is streamparse compatible with Python 3?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, streamparse is fully compatible with Python 3 starting with version 3.3
which we use in our `unit tests`_.

.. _unit tests: https://github.com/Parsely/streamparse/blob/master/.travis.yml

How can I contribute to streamparse?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please see the `CONTRIBUTING`_ document in Github

.. _CONTRIBUTING: https://github.com/Parsely/streamparse/blob/master/CONTRIBUTING.rst


How do I trigger some code before or after I submit my topology?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After you create a streamparse project using ``sparse quickstart``, you'll have
a ``fabfile.py`` in that directory. In that file, you can specify two
functions (``pre_submit`` and ``post_submit``) which are expected to accept four arguments:

* ``topology_name``: the name of the topology being submitted
* ``env_name``: the name of the environment where the topology is being
  submitted (e.g. ``"prod"``)
* ``env_config``: the relevant config portion from the ``config.json`` file for
  the environment you are submitting the topology to
* ``options``: the fully resolved Storm options

Here is a sample ``fabfile.py`` file that sends a message to IRC after a
topology is successfully submitted to prod.

.. code-block:: python

    # my_project/fabfile.py
    from __future__ import absolute_import, print_function, unicode_literals

    from my_project import write_to_irc


    def post_submit(topo_name, env_name, env_config):
        if env_name == "prod":
            write_to_irc("Deployed {} to {}".format(topo_name, env_name))


How should I install streamparse on the cluster nodes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

streamparse assumes your Storm servers have Python, pip, and virtualenv
installed.  After that, the installation of all required dependencies (including
streamparse itself) is taken care of via the `config.json` file for the
streamparse project and the ``sparse submit`` command.

Should I install Clojure?
~~~~~~~~~~~~~~~~~~~~~~~~~

No, the Java requirements for streamparse are identical to that of Storm itself.
Storm requires Java and `bundles Clojure as a requirement`_, so you do not need
to do any separate installation of Clojure.  You just need Java on all Storm
servers.

.. _bundles Clojure as a requirement: https://github.com/apache/storm/blob/5383ac375cb2955e3247d485e46f1f58bff62810/pom.xml#L320-L322

How do I deploy into a VPC?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Update your ``~/.ssh/config`` to use a bastion host inside your VPC for your
commands::

    Host *.internal.example.com
        ProxyCommand ssh bastion.example.com exec nc %h %p

If you don't have a common subdomain you'll have to list all of the hosts
individually::

    Host host1.example.com
        ProxyCommand ssh bastion.example.com exec nc %h %p
    ...

Set up your streamparse config to use all of the hosts normally (without bastion
host).

How do I override SSH settings?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is highly recommended that you just modify your ``~/.ssh/config`` file if you
need to tweak settings for setting up the SSH tunnel to your Nimbus server, but
you can also set your SSH password or port in your ``config.json`` by setting
the ``ssh_password`` or ``ssh_port`` environment settings.

.. code-block:: json

    {
        "topology_specs": "topologies/",
        "virtualenv_specs": "virtualenvs/",
        "envs": {
            "prod": {
                "user": "somebody",
                "ssh_password": "THIS IS A REALLY BAD IDEA",
                "ssh_port": 52,
                "nimbus": "streamparse-box",
                "workers": [
                    "streamparse-box"
                ],
                "virtualenv_root": "/data/virtualenvs"
            }
        }
    }


How do I dynamically generate the worker list?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a small cluster it's sufficient to specify the list of workers in ``config.json``.
However, if you have a large or complex environment where workers are numerous
or short-lived, ``streamparse`` supports querying the nimbus server for a list of hosts.

An undefined list (empty or None) of ``workers`` will trigger the lookup.
Explicitly defined hosts are preferred over a lookup.

Lookups are configured on a per-environment basis, so the ``prod`` environment
below uses the dynamic lookup, while ``beta`` will not.

.. code-block:: json

    {
        "topology_specs": "topologies/",
        "virtualenv_specs": "virtualenvs/",
        "envs": {
            "prod": {
                "nimbus": "streamparse-prod",
                "virtualenv_root": "/data/virtualenvs"
            },
            "beta": {
                "nimbus": "streamparse-beta",
                "workers": [
                    "streamparse-beta"
                ],
                "virtualenv_root": "/data/virtualenvs"
            }
        }
    }


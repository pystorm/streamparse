Developing Streamparse
======================

Lein
------

Install Leiningen according to the instructions in the quickstart.

Local pip installation
----------------------

In your virtualenv for this project, go into ``~/repos/streamparse`` (where you
cloned streamparse) and simply run::

    python setup.py develop

This will install a streamparse Python version into the virtualenv which is
essentially symlinked to your local version.

**NOTE:** streamparse currently pip installs streamparse's **released** version
on remote clusters automatically. Therefore, though this will work for local
development, you'll need to push streamparse somewhere pip installable (or
change requirements.txt) to make it pick up that version on a remote cluster.


Installing Storm pre-releases
-----------------------------

You can clone Storm from Github here::

    git clone git@github.com:apache/storm.git

There are tags available for releases, e.g.::

    git checkout v1.0.1

To build a local Storm release, use::

    mvn install
    cd storm-dist/binary
    mvn package

These steps will take awhile as they also run Storm's internal unit and
integration tests.

The first line will actually install Storm locally in your maven (.m2)
repository. You can confirm this with::

    ls ~/.m2/repository/org/apache/storm/storm-core/1.0.1

You should now be able to change your ``project.clj`` to include a reference to
this new release.

Once you change that, you can run::

    lein deps :tree | grep storm

To confirm it is using the upgraded Clojure 1.5.1 (changed in 0.9.2), run::

    lein repl

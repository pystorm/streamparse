streamparse
===========

|Build Status|

streamparse lets you run Python code against real-time streams of data. It also
integrates Python smoothly with Apache Storm.

It can be viewed as a more robust alternative to Python worker-and-queue
systems, as might be built atop frameworks like Celery and RQ. It offers a way
to do "real-time map/reduce style computation" against live streams of data. It
can also be a powerful way to scale long-running, highly parallel Python
processes in production.

|Demo|

Documentation
-------------

`http://streamparse.readthedocs.org/en/latest/ <http://streamparse.readthedocs.org/en/latest/>`__

User Group
----------

Follow the project's progress, get involved, submit ideas and ask for help via
our Google Group, `streamparse@googlegroups.com <https://groups.google.com/forum/#!forum/streamparse>`__.

Contributors
------------

Alphabetical, by last name:

-  Dan Blanchard (`@dsblanch <https://twitter.com/dsblanch>`__)
-  Keith Bourgoin (`@kbourgoin <https://twitter.com/kbourgoin>`__)
-  Jeffrey Godwyll (`@rey12rey <https://twitter.com/rey12rey>`__)
-  Andrew Montalenti (`@amontalenti <https://twitter.com/amontalenti>`__)
-  Mike Sukmanowsky (`@msukmanowsky <https://twitter.com/msukmanowsky>`__)

Roadmap
-------

See the `Roadmap <https://github.com/Parsely/streamparse/wiki/Roadmap>`__.

.. |Build Status| image:: https://travis-ci.org/Parsely/streamparse.svg?branch=master
   :target: https://travis-ci.org/Parsely/streamparse
.. |Demo| image:: https://raw.githubusercontent.com/Parsely/streamparse/master/doc/source/images/quickstart.gif

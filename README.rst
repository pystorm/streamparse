|logo|

|Build Status|

Streamparse lets you run Python code against real-time streams of data via
Apache Storm.  With streamparse you can create Storm bolts and spouts in
Python without having to write a single line of Java.  It also provides handy
CLI utilities for managing Storm clusters and projects.

The Storm/streamparse combo can be viewed as a more robust alternative to Python
worker-and-queue systems, as might be built atop frameworks like Celery and RQ.
It offers a way to do "real-time map/reduce style computation" against live
streams of data. It can also be a powerful way to scale long-running, highly
parallel Python processes in production.

|Demo|

Documentation
-------------

* `HEAD <http://streamparse.readthedocs.org/en/master/>`_
* `Stable <http://streamparse.readthedocs.org/en/stable/>`_

User Group
----------

Follow the project's progress, get involved, submit ideas and ask for help via
our Google Group, `streamparse@googlegroups.com <https://groups.google.com/forum/#!forum/streamparse>`__.

Contributors
------------

Alphabetical, by last name:

-  Dan Blanchard (`@dsblanch <https://twitter.com/dsblanch>`__)
-  Keith Bourgoin (`@kbourgoin <https://twitter.com/kbourgoin>`__)
-  Arturo Filastò (`@hellais <https://github.com/hellais>`__)
-  Jeffrey Godwyll (`@rey12rey <https://twitter.com/rey12rey>`__)
-  Daniel Hodges (`@hodgesds <https://github.com/hodgesds>`__)
-  Wieland Hoffmann (`@mineo <https://github.com/mineo>`__)
-  Tim Hopper (`@tdhopper <https://twitter.com/tdhopper>`__)
-  Omer Katz (`@thedrow <https://github.com/thedrow>`__)
-  Aiyesha Ma (`@Aiyesha <https://github.com/Aiyesha>`__)
-  Andrew Montalenti (`@amontalenti <https://twitter.com/amontalenti>`__)
-  Rohit Sankaran (`@roadhead <https://twitter.com/roadhead>`__)
-  Viktor Shlapakov (`@vshlapakov <https://github.com/vshlapakov>`__)
-  Mike Sukmanowsky (`@msukmanowsky <https://twitter.com/msukmanowsky>`__)
-  Cody Wilbourn (`@codywilbourn <https://github.com/codywilbourn>`__)
-  Curtis Vogt (`@omus <https://github.com/omus>`__)

Changelog
---------

See the `releases <https://github.com/Parsely/streamparse/releases>`__ page on
GitHub.

Roadmap
-------

See the `Roadmap <https://github.com/Parsely/streamparse/wiki/Roadmap>`__.

.. |logo| image:: https://raw.githubusercontent.com/Parsely/streamparse/master/doc/source/images/streamparse-logo.png
.. |Build Status| image:: https://travis-ci.org/Parsely/streamparse.svg?branch=master
   :target: https://travis-ci.org/Parsely/streamparse
.. |Demo| image:: https://raw.githubusercontent.com/Parsely/streamparse/master/doc/source/images/quickstart.gif

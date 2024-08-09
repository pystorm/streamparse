Creating a new Streamparse Release
==================================

First, update the version number in ``version.py`` using `semantic versioning <https://semver.org>`_.

Tag your commit with the new version number. For example::

   git tag -a v0.1.0 -m "v0.1.0"

Push the tag to GitHub::

   git push origin v0.1.0

Install twine and install build::

   pip install twine
   pip install build

Build the package::

   python -m build

Upload the package to test.pypi.org::

   twine upload --repository testpypi dist/*

*Verify you can install it.* Then, upload it to pypi.org::

   twine upload dist/*

*Again, verify it installs correctly.* Then, finally, create a new release on GitHub.

.. _SEMVER: https://semver.org

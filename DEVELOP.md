# streamparse Development

To build streamparse, we use the `invoke` library, which also happens to be an
actual dependency of the project.

To build an egg:

    invoke build

To also build Sphinx documentation:

    invoke build --docs

To run tests:

    invoke tests

To install development version into your virtualenv:

    invoke develop

Since invoke is still under heavy development, you may want to install it
directly from a cloned Github repo.

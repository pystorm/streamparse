import argparse
import unittest

from streamparse.cli import sparse


def test_load_subparsers():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    sparse.load_subparsers(subparsers)
    # grab subcommands from subparsers
    subcommands = parser._optionals._actions[1].choices.keys()
    # we know quickstart will be a subcommand test others as needed
    assert "quickstart" in subcommands

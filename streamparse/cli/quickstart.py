"""
Create new streamparse project template.
"""

from __future__ import absolute_import

from argparse import ArgumentDefaultsHelpFormatter as DefaultsHelpFormatter

from streamparse.bootstrap import quickstart


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('quickstart',
                                      formatter_class=DefaultsHelpFormatter,
                                      description=__doc__,
                                      help=__doc__)
    subparser.set_defaults(func=main)
    subparser.add_argument('project_name',
                           help='Name of new streamparse project.')


def main(args):
    """ Create new streamparse project template. """
    quickstart(args.project_name)

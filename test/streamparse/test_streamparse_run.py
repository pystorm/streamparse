"""
Tests for streamparse_run
"""

import logging
import os
import sys
import unittest

from streamparse import run


class StreamparseRunTests(unittest.TestCase):

    run_target_invoked = False
    run_target_invoked_serializer = None

    def test_streamparse_run_storm_1_0_2(self):
        # patch streamparse_run sys argv assuming tests run
        # from streamparse project root, (Storm <= 1.0.2 case)
        sys.argv = ['streamparse_run',
                    'test.'
                    'streamparse_run.streamparse_run_target.StreamparseRunTarget']
        StreamparseRunTests.run_target_invoked = False
        StreamparseRunTests.run_target_invoked_serializer = None
        run.main()
        self.assertTrue(StreamparseRunTests.run_target_invoked)
        self.assertEquals('json', StreamparseRunTests.run_target_invoked_serializer)

    def test_streamparse_run_storm_1_0_3(self):
        # patch streamparse_run resources path and sys argv
        # assuming tests run from streamparse project root,
        # (Storm >= 1.0.3 case)
        run.RESOURCES_PATH = 'test'
        sys.argv = ['streamparse_run',
                    'streamparse_run.streamparse_run_target.StreamparseRunTarget '
                    '--serializer=msgpack']
        StreamparseRunTests.run_target_invoked = False
        StreamparseRunTests.run_target_invoked_serializer = None
        run.main()
        self.assertTrue(StreamparseRunTests.run_target_invoked)
        self.assertEquals('msgpack', StreamparseRunTests.run_target_invoked_serializer)

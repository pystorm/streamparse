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
        # from streamparse project root, (the Storm <= 1.0.2 case):
        # target test run module specifying absolute import path
        # including 'test' folder
        sys.argv = [
            "streamparse_run",
            "test.streamparse_run.streamparse_run_target.StreamparseRunTarget",
        ]
        # invoke run module main
        StreamparseRunTests.run_target_invoked = False
        StreamparseRunTests.run_target_invoked_serializer = None
        run.main()
        self.assertTrue(StreamparseRunTests.run_target_invoked)
        self.assertEquals("json", StreamparseRunTests.run_target_invoked_serializer)

    def test_streamparse_run_storm_1_0_3(self):
        # patch streamparse_run resources path and sys argv
        # assuming tests run from streamparse project root
        # with 'extra' resources folder, (Storm >= 1.0.3 case):
        # target test run module specifying relative import
        # path within 'test' resources folder; also test
        # serializer option
        run.RESOURCES_PATH = "test"
        sys.argv = [
            "streamparse_run",
            "streamparse_run.streamparse_run_target.StreamparseRunTarget --serializer=msgpack",
        ]
        # invoke run module main
        StreamparseRunTests.run_target_invoked = False
        StreamparseRunTests.run_target_invoked_serializer = None
        run.main()
        self.assertTrue(StreamparseRunTests.run_target_invoked)
        self.assertEquals("msgpack", StreamparseRunTests.run_target_invoked_serializer)

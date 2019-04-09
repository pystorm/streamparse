"""
Test target for streamparse_run
"""

from test.streamparse.test_streamparse_run import StreamparseRunTests


class StreamparseRunTarget:
    def __init__(self, serializer):
        self.serializer = serializer

    def run(self):
        StreamparseRunTests.run_target_invoked = True
        StreamparseRunTests.run_target_invoked_serializer = self.serializer

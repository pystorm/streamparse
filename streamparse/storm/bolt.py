"""
Module to add streamparse-specific extensions to pystorm Bolt classes
"""

import pystorm

from .component import Component

class Bolt(pystorm.bolt.Bolt, Component):
    """pystorm Bolt with streamparse-specific additions"""
    pass

class BatchingBolt(pystorm.bolt.BatchingBolt, Bolt):
    """pystorm BatchingBolt with streamparse-specific additions"""
    pass


class TicklessBatchingBolt(pystorm.bolt.TicklessBatchingBolt, BatchingBolt):
    """pystorm TicklessBatchingBolt with streamparse-specific additions"""
    pass

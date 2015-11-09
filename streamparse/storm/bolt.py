"""
Module to add streamparse-specific extensions to pystorm Bolt classes
"""

import pystorm

from .component import Component
from ..dsl.bolt import ShellBoltSpec


class ShellBolt(Component):
    @classmethod
    def spec(cls, name=None, command=None, script=None, inputs=None,
             parallelism=None, config=None, outputs=None):
        return ShellBoltSpec(cls, command=command, script=script, name=name,
                             inputs=inputs, parallelism=parallelism,
                             config=config, outputs=outputs)


class Bolt(pystorm.bolt.Bolt, ShellBolt):
    """pystorm Bolt with streamparse-specific additions"""
    @classmethod
    def spec(cls, name=None, inputs=None, parallelism=None, config=None):
        return ShellBoltSpec(cls, command='python',
                             script=('-m streamparse.runner {}'
                                     .format(cls.__name__)),
                             name=name, inputs=inputs, parallelism=parallelism,
                             config=config, outputs=cls.outputs)


class BatchingBolt(pystorm.bolt.BatchingBolt, Bolt):
    """pystorm BatchingBolt with streamparse-specific additions"""
    pass


class TicklessBatchingBolt(pystorm.bolt.TicklessBatchingBolt, BatchingBolt):
    """pystorm TicklessBatchingBolt with streamparse-specific additions"""
    pass

"""
Module to add streamparse-specific extensions to pystorm Bolt classes
"""

import pystorm

from ..dsl.bolt import JavaBoltSpec, ShellBoltSpec
from .component import Component


class JavaBolt(Component):
    @classmethod
    def spec(cls, name=None, serialized_java=None, full_class_name=None,
             args_list=None, inputs=None, par=1, config=None, outputs=None):
        return JavaBoltSpec(cls, name=name, serialized_java=serialized_java,
                            full_class_name=full_class_name,
                            args_list=args_list, inputs=inputs, par=par,
                            config=config, outputs=outputs)


class ShellBolt(Component):
    @classmethod
    def spec(cls, name=None, command=None, script=None, inputs=None,
             par=None, config=None, outputs=None):
        return ShellBoltSpec(cls, command=command, script=script, name=name,
                             inputs=inputs, par=par,
                             config=config, outputs=outputs)


class Bolt(pystorm.bolt.Bolt, ShellBolt):
    """pystorm Bolt with streamparse-specific additions"""
    @classmethod
    def spec(cls, name=None, inputs=None, par=None, config=None):
        return ShellBoltSpec(cls, command='python',
                             script='-m streamparse.run {}'.format(cls.__name__),
                             name=name, inputs=inputs, par=par,
                             config=config, outputs=cls.outputs)


class BatchingBolt(pystorm.bolt.BatchingBolt, Bolt):
    """pystorm BatchingBolt with streamparse-specific additions"""
    pass


class TicklessBatchingBolt(pystorm.bolt.TicklessBatchingBolt, BatchingBolt):
    """pystorm TicklessBatchingBolt with streamparse-specific additions"""
    pass

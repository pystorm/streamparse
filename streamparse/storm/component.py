"""
Module to add streamparse-specific extensions to pystorm Component classes
"""
import pystorm

from ..dsl.component import ComponentSpecification


class Component(pystorm.component.Component):
    """pystorm Component with streamparse-specific additions"""
    outputs = None
    parallelism = 1
    config = None

    @classmethod
    def spec(cls, name=None, inputs=None, parallelism=None, config=None):
        return ComponentSpecification(cls, name=name, inputs=inputs,
                                      parallelism=parallelism,
                                      config=config, outputs=cls.outputs)

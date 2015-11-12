"""
Module to add streamparse-specific extensions to pystorm Component classes
"""
import pystorm

from ..dsl.component import ComponentSpec


class Component(pystorm.component.Component):
    """pystorm Component with streamparse-specific additions"""
    outputs = None
    par = 1
    config = None

    @classmethod
    def spec(cls, name=None, inputs=None, par=None, config=None):
        return ComponentSpec(cls, name=name, inputs=inputs, par=par,
                             config=config, outputs=cls.outputs)

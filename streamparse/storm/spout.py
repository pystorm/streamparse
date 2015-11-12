"""
Module to add streamparse-specific extensions to pystorm Spout class
"""

import pystorm

from .component import Component
from ..dsl.spout import ShellSpoutSpec


class ShellSpout(Component):
    @classmethod
    def spec(cls, name=None, command=None, script=None, parallelism=None,
             config=None, outputs=None):
        return ShellSpoutSpec(cls, command=command, script=script, name=name,
                              parallelism=parallelism, config=config,
                              outputs=outputs)


class Spout(pystorm.spout.Spout, ShellSpout):
    """pystorm Spout with streamparse-specific additions"""
    @classmethod
    def spec(cls, name=None, parallelism=None, config=None):
        return ShellSpoutSpec(cls, command='python',
                              script='-m streamparse.run {}'.format(cls.__name__),
                              name=name, parallelism=parallelism, config=config,
                              outputs=cls.outputs)

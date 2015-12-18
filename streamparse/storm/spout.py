"""
Module to add streamparse-specific extensions to pystorm Spout class
"""

import pystorm

from ..dsl.spout import JavaSpoutSpec, ShellSpoutSpec
from .component import Component


class JavaSpout(Component):
    @classmethod
    def spec(cls, name=None, serialized_java=None, full_class_name=None,
             args_list=None, par=1, config=None, outputs=None):
        return JavaSpoutSpec(cls, name=name, serialized_java=serialized_java,
                            full_class_name=full_class_name,
                            args_list=args_list, par=par,
                            config=config, outputs=outputs)


class ShellSpout(Component):
    @classmethod
    def spec(cls, name=None, command=None, script=None, par=None, config=None,
             outputs=None):
        return ShellSpoutSpec(cls, command=command, script=script, name=name,
                              par=par, config=config, outputs=outputs)


class Spout(pystorm.spout.Spout, ShellSpout):
    """pystorm Spout with streamparse-specific additions"""
    @classmethod
    def spec(cls, name=None, par=None, config=None):
        return ShellSpoutSpec(cls, command='streamparse_run',
                              script='{}.{}'.format(cls.__module__,
                                                    cls.__name__),
                              name=name, par=par, config=config,
                              outputs=cls.outputs)

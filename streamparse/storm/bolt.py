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
        """Create a :class:`~streamparse.dsl.bolt.ShellBoltSpec`.

        This spec represents this Component in a :class:`~streamparse.Topology`.

        :param component_cls:  Class this ShellBoltSpec represents.
        :type component_cls:   `class`
        :param name:   Name of this component.  Defaults to name of class.
        :type name:    `str`
        :param command:  Path to command the Storm will execute.
        :type command: `str`
        :param script: Arguments to `command`.  Multiple arguments should just
                       be separated by spaces.
        :type command: `str`
        :param inputs: Streams that feed into this Component. Only makes sense
                       for :class:`~streamparse.Bolt`, as
                       :class:`~streamparse.Spout` instances do not receive
                       tuples.

                       Two forms of this are acceptable:

                       1.  A `dict` mapping from
                           :class:`~streamparse.dsl.component.ComponentSpec` to
                           :class:`~streamparse.Grouping`.
                       2.  A `list` of :class:`~streamparse.Stream` or
                           :class:`~streamparse.dsl.component.ComponentSpec`.
        :param par:    Parallelism hint for this Component.  For Python
                       Components, this works out to be the number of Python
                       processes running it in the the topology (across all
                       machines).  See :ref:`parallelism`.
        :type par:     `int`
        :param config: Component-specific config settings to pass to Storm.
        :type config:  `dict`
        :param outputs: Outputs this
        """
        return ShellBoltSpec(cls, command=command, script=script, name=name,
                             inputs=inputs, par=par,
                             config=config, outputs=outputs)


class Bolt(pystorm.bolt.Bolt, ShellBolt):
    """pystorm Bolt with streamparse-specific additions"""
    @classmethod
    def spec(cls, name=None, inputs=None, par=None, config=None):
        return ShellBoltSpec(cls, command='streamparse_run',
                             script='{}.{}'.format(cls.__module__,
                                                   cls.__name__),
                             name=name, inputs=inputs, par=par,
                             config=config, outputs=cls.outputs)


class BatchingBolt(pystorm.bolt.BatchingBolt, Bolt):
    """pystorm BatchingBolt with streamparse-specific additions"""
    pass


class TicklessBatchingBolt(pystorm.bolt.TicklessBatchingBolt, BatchingBolt):
    """pystorm TicklessBatchingBolt with streamparse-specific additions"""
    pass

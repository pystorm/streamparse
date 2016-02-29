"""
Module to add streamparse-specific extensions to pystorm Component classes
"""
import pystorm
from pystorm.component import StormHandler  # This is used by other code

from ..dsl.component import ComponentSpec


class Component(pystorm.component.Component):
    """pystorm Component with streamparse-specific additions

    :ivar outputs: The outputs
    :ivar config: Component-specific config settings to pass to Storm.
    """
    outputs = None
    par = 1
    config = None

    @classmethod
    def spec(cls, name=None, inputs=None, par=None, config=None):
        """Create a :class:`~streamparse.dsl.component.ComponentSpec`.

        This spec represents this Component in a :class:`~streamparse.Topology`.

        :param name:   Name of this component.  Defaults to name of class.
        :type name:    `str`
        :param inputs: Streams that feed into this Component. Only makes sense
                       for :class:`~streamparse.Bolt`, as
                       :class:`~streamparse.Spout` instances do not receive
                       tuples.

                       Two forms of this are acceptable:

                       1.  A `dict` mapping from `ComponentSpec`s to tuple
                           groupings.
                       2.  A `list` of :class:`streamparse.Stream`s or
                           `ComponentSpec`s .
        :param par:    Parallelism hint for this Component.  For Python
                       Components, this works out to be the number of Python
                       processes running it in the the topology (across all
                       machines).  See :ref:`parallelism`.
        :type par:     `int`
        :param config: Component-specific config settings to pass to Storm.
        :type config:  `dict`
        """
        return ComponentSpec(cls, name=name, inputs=inputs, par=par,
                             config=config, outputs=cls.outputs)

"""
Module to add streamparse-specific extensions to pystorm Component classes
"""
import pystorm
from pystorm.component import StormHandler  # This is used by other code


class Component(pystorm.component.Component):
    """pystorm Component with streamparse-specific additions

    :ivar outputs: The outputs
    :ivar config: Component-specific config settings to pass to Storm.
    """

    outputs = None
    par = 1
    config = None

    @classmethod
    def spec(cls, *args, **kwargs):
        """This method exists only to give a more informative error message."""
        raise TypeError(
            f"Specifications should either be bolts or spouts. Given: {cls!r}"
        )

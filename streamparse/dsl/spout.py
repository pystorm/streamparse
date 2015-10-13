"""
Spout Specification

This module is called spout to mirror organization of storm package.
"""
from __future__ import absolute_import

from pystorm.spout import Spout

from .component import Specification


class SpoutSpecification(Specification):
    def __init__(self, component_cls, **kwargs):
        if not issubclass(component_cls, Spout):
            raise TypeError("Invalid spout: {}".format(component_cls))

        return super(SpoutSpecification, self).__init__(component_cls, **kwargs)

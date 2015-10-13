"""
Component-level Specification

This module is called component to mirror organization of storm package.
"""
from __future__ import absolute_import

from copy import deepcopy

from pystorm.component import Component


class Specification(object):
    def __init__(self, component_cls, name=None, parallelism=1):
        if not issubclass(component_cls, Component):
            raise TypeError("Invalid component: {}".format(component_cls))

        if not isinstance(parallelism, int) or parallelism < 1:
            raise ValueError("Parallelism must be a integer greater than 0")

        self.component_cls = component_cls
        self.name = name
        self.parallelism = parallelism

    def resolve_dependencies(self, specifications):
        """Allows specification subclasses to resolve an dependencies
        that they may have on other specifications.

        :param specifications: all of the specification objects for this
                               topology.
        :type specifications: dict
        """
        pass

    def __repr__(self):
        """:returns: A string representation of the Specification. """
        attr_dict = deepcopy(self.__dict__)
        component_cls = attr_dict.pop('component_cls')
        repr_str = '{}({cls}'.format(self.__class__.__name__,
                                     cls=component_cls.__name__)
        for key, val in attr_dict.items():
            repr_str += ', {}={!r}'.format(key, val)
        repr_str += ')'
        return repr_str
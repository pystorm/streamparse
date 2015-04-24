"""
Component-level Specification

This module is called component to mirror organization of storm package.
"""

from ..storm.component import Component


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
"""
Component-level Specification

This module is called component to mirror organization of pystorm package.
"""
from __future__ import absolute_import

from copy import deepcopy

import simplejson as json
from pystorm.component import Component

from .storm_thrift import ComponentCommon, StreamInfo


class ComponentSpecification(object):
    def __init__(self, component_cls, name=None, parallelism=1, config=None,
                 output_fields=None):
        if not issubclass(component_cls, Component):
            raise TypeError("Invalid component: {}".format(component_cls))

        if not isinstance(parallelism, int) or parallelism < 1:
            raise ValueError("Parallelism must be a integer greater than 0")

        self.component_cls = component_cls
        self.name = name
        self.common = ComponentCommon(inputs={}, streams={},
                                      parallelism_hint=parallelism)
        if config is not None:
            self.common.json_conf = json.dumps(config)

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

    def _get_common(self):
        """:returns: A ``storm_thrift.ComponentCommon`` object representing the
                     ``inputs``, ``streams``, ``parallelism_hint``, and
                     ``json_conf`` for this component.
        """
        if hasattr(self, 'sources'):


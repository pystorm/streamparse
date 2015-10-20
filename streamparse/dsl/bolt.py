"""
Bolt Specification

This module is called bolt to mirror organization of storm package.
"""
from __future__ import absolute_import

from collections import Iterable

import thriftpy
from pystorm.bolt import Bolt
from six import string_types

from . import storm_thrift
from .component import ComponentSpecification
from .topology import Grouping, TopologyError


class ShellBolt(object):


class BoltSpecification(ComponentSpecification):
    def __init__(self, component_cls, source=None, group_on=Grouping.SHUFFLE,
                 **kwargs):
        if not issubclass(component_cls, Bolt):
            raise TypeError("Invalid bolt: {}".format(component_cls))

        super(BoltSpecification, self).__init__(component_cls, **kwargs)

        # Ensure that the source is always a list.
        if isinstance(source, string_types):
            sources = [source]
        elif isinstance(source, Iterable):
            sources = list(source)
        elif source:
            sources = [source]
        else:
            raise TopologyError('{} component "{}" requires at least one source'
                                .format(self.component_cls.__name__, self.name))

        if not Grouping.valid(group_on):
            raise TypeError('Invalid group_on given: {}'.format(group_on))

        self.sources = sources
        self.group_on = group_on

    def resolve_dependencies(self, specifications):
        """Modifies the bolt's sources to be references to other Specification
        objects. Also ensures that group_on fields are provided by the
        source Specifications.

        :param specifications: all of the specification objects for this
                               topology.
        :type specifications: dict
        """
        for i, source in enumerate(self.sources):

            # Resolve sources that are not a specification object.
            if not isinstance(source, Specification):
                if source in specifications:
                    self.sources[i] = specifications[source]
                else:
                    raise TopologyError('Missing source named {} from {}'
                                        .format(source, self))

                # Ensure that source always references a specification object.
                source = self.sources[i]

            # Ensure that group on field names exist in the source.
            if isinstance(self.group_on, list):
                outputs = source.component_cls.streams

                for group in self.group_on:
                    if group not in outputs:
                        raise TopologyError('Field {} does not exist in source '
                                            '{} as an output'.format(group,
                                                                     outputs))

    def to_thrift(self):
        """:returns: A ``storm_thrift.Bolt`` object to be serialized as part of
                     a Storm Thrift topology.
        """
        bolt_spec = storm_thrift.Bolt()
        shell_object = storm_thrift.ShellComponent()
        shell_object.execution_command = bolt_spec.execution_command
        shell_object.script = bolt_spec.script
        bolt_spec.spout_object = ComponentObject()
        bolt_spec.spout_object.shell = shell_object
        bolt_spec.common = self._getComponentCommon(spoutId, spout)

        common = self._commons[id]
        stream_info = storm_thrift.StreamInfo()
        stream_info.output_fields = component.declareOutputFields()
        stream_info.direct = False # Appears to be unused by Storm
        common.streams['default'] = stream_info





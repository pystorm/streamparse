"""
Topology base class
"""
from __future__ import absolute_import

from six import add_metaclass, iteritems, string_types
from thriftpy.transport import TMemoryBuffer
from thriftpy.protocol import TBinaryProtocol

from .bolt import BoltSpecification
from .component import Specification
from .spout import SpoutSpecification
from .storm_thrift import (ComponentCommon, Grouping, NullStruct, GlobalStreamId,
                           StreamInfo, SpoutSpec, ShellComponent,
                           ComponentObject, StormTopology)
from .storm_thrift import Bolt as BoltSpec


class Grouping(object):
    SHUFFLE = ":shuffle"
    GLOBAL = ":global"
    DIRECT = ":direct"
    ALL = ":all"

    @classmethod
    def fields(cls, *fieldlist):
        return list(fieldlist)

    @classmethod
    def valid(cls, grouping):
        return (isinstance(grouping, list) or grouping in (Grouping.SHUFFLE,
                                                           Grouping.GLOBAL,
                                                           Grouping.DIRECT,
                                                           Grouping.ALL))


class TopologyType(type):
    def __new__(mcs, classname, bases, class_dict):
        specs = {}
        bolt_specs = {}
        spout_specs = {}
        for spoutId, spout in self._spouts.iteritems():
            spout_spec = SpoutSpec()
            shell_object = ShellComponent()
            shell_object.execution_command = spout.execution_command
            shell_object.script = spout.script
            spout_spec.spout_object = ComponentObject()
            spout_spec.spout_object.shell = shell_object
            spout_spec.common = self._getComponentCommon(spoutId, spout)
            spout_specs[spoutId] = spout_spec

        topology = StormTopology(spouts=spout_specs, bolts=bolt_specs,
                                 state_spouts={})
        for name, spec in iteritems(class_dict):
            if isinstance(spec, Specification):

                # Use the variable name as the specification name.
                if spec.name is None:
                    spec.name = name

                if spec.name not in specs:
                    specs[spec.name] = spec.to_thrift_spec()
                else:
                    raise TopologyError("Duplicate specification name: {}"
                                        .format(spec.name))

                if isinstance(spec, BoltSpecification):
                    bolt_specs[specs[spec.name].id] =

        class_dict["specs"] = list(specs.values())

        # Resolve dependencies in specifications.
        for name, spec in iteritems(specs):
            spec.resolve_dependencies(specs)

        return type.__new__(mcs, classname, bases, class_dict)


@add_metaclass(TopologyType)
class Topology(object):
    def __repr__(self):
        """:returns: A string representation of the topology"""
        return repr(self.specs)

    def to_thrift(self):

        return topology

    def write(self, stream):
        """Writes the topology to a stream or file."""
        topology = self.createTopology()
        def write_it(stream):
            transport_out = TMemoryBuffer()
            protocol_out = TBinaryProtocol(transport_out)
            topology.write(protocol_out)
            transport_bytes = transport_out.getvalue()
            stream.write(transport_bytes)

        if isinstance(stream, string_types):
            with open(stream, 'wb') as f:
                write_it(f)
        else:
            write_it(stream)

        return topology

    def read(self, stream):
        """Reads the topology from a stream or file."""
        def read_it(stream):
            stream_bytes = stream.read()
            transport_in = TMemoryBuffer(stream_bytes)
            protocol_in = TBinaryProtocol(transport_in)
            topology = StormTopology()
            topology.read(protocol_in)
            return topology

        if isinstance(stream, string_types):
            with open(stream, 'rb') as f:
                return read_it(f)
        else:
            return read_it(stream)

    def _getComponentCommon(self, id, component):
        common = self._commons[id]
        stream_info = StreamInfo()
        stream_info.output_fields = component.declareOutputFields()
        stream_info.direct = False # Appears to be unused by Storm
        common.streams['default'] = stream_info

        return common

class TopologyError(Exception):
    pass

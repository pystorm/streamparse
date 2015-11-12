"""
Topology base class
"""
from __future__ import absolute_import

from pystorm.component import Component
from six import add_metaclass, iteritems, iterkeys, string_types
from thriftpy.transport import TMemoryBuffer
from thriftpy.protocol import TBinaryProtocol

from .bolt import JavaBoltSpec, ShellBoltSpec
from .component import ComponentSpec
from .exceptions import TopologyError
from .spout import JavaSpoutSpec, ShellSpoutSpec
from .thrift import storm_thrift


class TopologyType(type):
    def __new__(mcs, classname, bases, class_dict):
        specs = {}
        bolt_specs = {}
        spout_specs = {}
        # Set names first
        for name, spec in iteritems(class_dict):
            if isinstance(spec, ComponentSpec):
                # Use the variable name as the specification name.
                if spec.name is None:
                    spec.name = name
                if spec.name in specs:
                    raise TopologyError("Duplicate specification name: {}"
                                        .format(spec.name))
        # Perform other checks
        for name, spec in iteritems(class_dict):
            if isinstance(spec, ComponentSpec):
                if isinstance(spec, (JavaBoltSpec, ShellBoltSpec)):
                    specs[spec.name] = spec
                    if not spec.inputs:
                        raise TopologyError('{} component "{}" requires at '
                                            'least one input'
                                            .format(spec.component_cls.__name__,
                                                    spec.name))
                    bolt_specs[spec.name] = storm_thrift.Bolt(
                        bolt_object=spec.component_object, common=spec.common)
                elif isinstance(spec, (JavaSpoutSpec, ShellSpoutSpec)):
                    specs[spec.name] = spec
                    if not spec.outputs:
                        raise TopologyError('{} component "{}" requires at '
                                            'least one output'
                                            .format(spec.component_cls.__name__,
                                                    spec.name))
                    spout_specs[spec.name] = storm_thrift.SpoutSpec(
                        spout_object=spec.component_object, common=spec.common)
                else:
                    raise TopologyError('Specifications should either be bolts '
                                        'or spouts.  Given: {!r}'.format(spec))
                # Clean up ComponentSpec componentIds in inputs
                if spec.inputs is None:
                    spec.inputs = {}
                for stream_id, grouping in list(iteritems(spec.inputs)):
                    if isinstance(stream_id.componentId, ComponentSpec):
                        # Have to reinsert key after fix because hash changes
                        del spec.inputs[stream_id]
                        stream_id.componentId = stream_id.componentId.name
                        spec.inputs[stream_id] = grouping
                    # This should never happen, but it's worth checking for
                    elif stream_id.componentId is None:
                        raise TopologyError('GlobalStreamId.componentId should '
                                            'not be None.')

            elif isinstance(spec, Component):
                raise TopologyError('Topology objects should only have '
                                    'ComponentSpec attributes.  Did you forget '
                                    'to call the spec class method for your '
                                    'component?  Given: {!r}'.format(spec))
        class_dict['thrift_bolts'] = bolt_specs
        class_dict['thrift_spouts'] = spout_specs
        class_dict['specs'] = list(specs.values())
        class_dict['_topology'] = storm_thrift.StormTopology(spouts=spout_specs,
                                                             bolts=bolt_specs,
                                                             state_spouts={})
        return type.__new__(mcs, classname, bases, class_dict)

    def __repr__(cls):
        """:returns: A string representation of the topology"""
        return repr(cls._topology)


@add_metaclass(TopologyType)
class Topology(object):
    """
    Class to define a Storm topology in a Python DSL.
    """
    @classmethod
    def write(cls, stream):
        """Writes the topology to a stream or file."""
        def write_it(stream):
            transport_out = TMemoryBuffer()
            protocol_out = TBinaryProtocol(transport_out)
            cls._topology.write(protocol_out)
            transport_bytes = transport_out.getvalue()
            stream.write(transport_bytes)

        if isinstance(stream, string_types):
            with open(stream, 'wb') as output_file:
                write_it(output_file)
        else:
            write_it(stream)

    @classmethod
    def read(cls, stream):
        """Reads the topology from a stream or file."""
        def read_it(stream):
            stream_bytes = stream.read()
            transport_in = TMemoryBuffer(stream_bytes)
            protocol_in = TBinaryProtocol(transport_in)
            topology = storm_thrift.StormTopology()
            topology.read(protocol_in)
            return topology

        if isinstance(stream, string_types):
            with open(stream, 'rb') as input_file:
                return read_it(input_file)
        else:
            return read_it(stream)

"""
Topology base class
"""
from __future__ import absolute_import

from pystorm.component import Component
from six import add_metaclass, iteritems, itervalues, string_types
from thriftpy.transport import TMemoryBuffer
from thriftpy.protocol import TBinaryProtocol

from ..thrift import storm_thrift
from .bolt import JavaBoltSpec, ShellBoltSpec
from .component import ComponentSpec
from .spout import JavaSpoutSpec, ShellSpoutSpec


class TopologyType(type):
    """
    Class to define a Storm topology in a Python DSL.
    """
    def __new__(mcs, classname, bases, class_dict):
        bolt_specs = {}
        spout_specs = {}
        # Copy ComponentSpec items out of class_dict
        specs = TopologyType.class_dict_to_specs(class_dict)
        # Perform checks
        for spec in itervalues(specs):
            if isinstance(spec, (JavaBoltSpec, ShellBoltSpec)):
                TopologyType.add_bolt_spec(spec, bolt_specs)
            elif isinstance(spec, (JavaSpoutSpec, ShellSpoutSpec)):
                TopologyType.add_spout_spec(spec, spout_specs)
            else:
                raise TypeError('Specifications should either be bolts or '
                                'spouts.  Given: {!r}'.format(spec))
            TopologyType.clean_spec_inputs(spec, specs)
        if classname != 'Topology' and not spout_specs:
            raise ValueError('A Topology requires at least one Spout')
        class_dict['thrift_bolts'] = bolt_specs
        class_dict['thrift_spouts'] = spout_specs
        class_dict['specs'] = list(specs.values())
        class_dict['_topology'] = storm_thrift.StormTopology(spouts=spout_specs,
                                                             bolts=bolt_specs,
                                                             state_spouts={})
        return type.__new__(mcs, classname, bases, class_dict)

    @classmethod
    def class_dict_to_specs(mcs, class_dict):
        """
        Takes a class `__dict__` and returns the `ComponentSpec` entries
        """
        specs = {}
        # Set spec names first
        for name, spec in iteritems(class_dict):
            if isinstance(spec, ComponentSpec):
                # Use the variable name as the specification name.
                if spec.name is None:
                    spec.name = name
                if spec.name in specs:
                    raise ValueError("Duplicate component name: {}"
                                     .format(spec.name))
                else:
                    specs[spec.name] = spec
            elif isinstance(spec, Component):
                raise TypeError('Topology classes should only have '
                                'ComponentSpec attributes.  Did you forget to '
                                'call the spec class method for your component?'
                                ' Given: {!r}'.format(spec))
        return specs

    @classmethod
    def add_bolt_spec(mcs, spec, bolt_specs):
        """
        Adds valid Bolt specs to `bolt_specs`, and raises exceptions for others.
        """
        if not spec.inputs:
            cls_name = spec.component_cls.__name__
            raise ValueError('{} "{}" requires at least one input, because it '
                             'is a Bolt.'.format(cls_name, spec.name))
        bolt_specs[spec.name] = storm_thrift.Bolt(bolt_object=spec.component_object,
                                                  common=spec.common)

    @classmethod
    def add_spout_spec(mcs, spec, spout_specs):
        """
        Adds valid Spout specs to `spout_specs`, and raises exceptions for others.
        """
        if not spec.outputs:
            cls_name = spec.component_cls.__name__
            raise ValueError('{} "{}" requires at least one output, because it '
                             'is a Spout'.format(cls_name, spec.name))
        spout_specs[spec.name] = storm_thrift.SpoutSpec(spout_object=spec.component_object,
                                                        common=spec.common)

    @classmethod
    def clean_spec_inputs(mcs, spec, specs):
        """
        Converts `spec.inputs` to a dict mapping from stream IDs to groupings.
        """
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
                raise TypeError('GlobalStreamId.componentId cannot be None.')
            # Check for invalid fields grouping
            stream_comp = specs[stream_id.componentId]
            valid_fields = set(stream_comp.outputs[stream_id.streamId]
                               .output_fields)
            if grouping.fields is not None:
                for field in grouping.fields:
                    if field not in valid_fields:
                        raise ValueError('Field {!r} specified in grouping is '
                                         'not a valid output field for the {!r}'
                                         ' {!r} stream.'.format(field,
                                                                stream_comp.name,
                                                                stream_id.streamId))

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
        """Write the topology to a stream or file.

        Typically used to write to Nimbus.

        .. note::
            This will not save the `specs` attribute, as that is not part of
            the Thrift output.
        """
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
        """Read a topology from a stream or file.

        .. note::
            This will not properly reconstruct the `specs` attribute, as that is
            not included in the Thrift output.
        """
        def read_it(stream):
            stream_bytes = stream.read()
            transport_in = TMemoryBuffer(stream_bytes)
            protocol_in = TBinaryProtocol(transport_in)
            topology = storm_thrift.StormTopology()
            topology.read(protocol_in)
            cls._topology = topology
            cls.thrift_bolts = topology.bolts
            cls.thrift_spouts = topology.spouts
            # Can't reconstruct Python specs from Thrift.
            cls.specs = []

        if isinstance(stream, string_types):
            with open(stream, 'rb') as input_file:
                return read_it(input_file)
        else:
            return read_it(stream)

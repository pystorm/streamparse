"""
Topology base class
"""
from __future__ import absolute_import

from copy import deepcopy

import simplejson as json
from pystorm.component import Component
from six import add_metaclass, iteritems, itervalues, string_types
from thriftpy.transport import TMemoryBuffer
from thriftpy.protocol import TBinaryProtocol

from ..thrift import storm_thrift
from .bolt import JavaBoltSpec, ShellBoltSpec
from .component import ComponentSpec, ShellComponentSpec
from .spout import JavaSpoutSpec, ShellSpoutSpec
from .util import to_python_arg_list


class TopologyType(type):
    """Class to define a Storm topology in a Python DSL."""

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
        if 'config' in class_dict:
            config_dict = class_dict['config']
            if not isinstance(config_dict, dict):
                raise TypeError('Topology config must be a dictionary. Given: '
                                '{!r}'.format(config_dict))
        else:
            class_dict['config'] = {}
        class_dict['thrift_bolts'] = bolt_specs
        class_dict['thrift_spouts'] = spout_specs
        class_dict['specs'] = list(specs.values())
        class_dict['thrift_topology'] = storm_thrift.StormTopology(spouts=spout_specs,
                                                                   bolts=bolt_specs,
                                                                   state_spouts={})
        return type.__new__(mcs, classname, bases, class_dict)

    @classmethod
    def class_dict_to_specs(mcs, class_dict):
        """Extract valid `ComponentSpec` entries from `Topology.__dict__`."""
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
                raise TypeError('Topology classes should have ComponentSpec '
                                'attributes.  Did you forget to call the spec '
                                'class method for your component?  Given: {!r}'
                                .format(spec))
        return specs

    @classmethod
    def add_bolt_spec(mcs, spec, bolt_specs):
        """Add valid Bolt specs to `bolt_specs`; raise exceptions for others."""
        if not spec.inputs:
            cls_name = spec.component_cls.__name__
            raise ValueError('{} "{}" requires at least one input, because it '
                             'is a Bolt.'.format(cls_name, spec.name))
        bolt_specs[spec.name] = storm_thrift.Bolt(bolt_object=spec.component_object,
                                                  common=spec.common)

    @classmethod
    def add_spout_spec(mcs, spec, spout_specs):
        """Add valid Spout specs to `spout_specs`; raise exceptions for others.
        """
        if not spec.outputs:
            cls_name = spec.component_cls.__name__
            raise ValueError('{} "{}" requires at least one output, because it '
                             'is a Spout'.format(cls_name, spec.name))
        spout_specs[spec.name] = storm_thrift.SpoutSpec(spout_object=spec.component_object,
                                                        common=spec.common)

    @classmethod
    def clean_spec_inputs(mcs, spec, specs):
        """Convert `spec.inputs` to a dict mapping from stream IDs to groupings.
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
        return repr(getattr(cls, '_topology', None))


@add_metaclass(TopologyType)
class Topology(object):
    """Class to define a Storm topology in a Python DSL."""
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

    @staticmethod
    def _spec_to_flux_dict(spec):
        """Convert a ComponentSpec into a dict as expected by Flux"""
        flux_dict = {'id': spec.name,
                     'constructorArgs': []}
        if isinstance(spec, ShellComponentSpec):
            if isinstance(spec, ShellBoltSpec):
                flux_dict['className'] = 'org.apache.storm.flux.wrappers.bolts.FluxShellBolt'
            else:
                flux_dict['className'] = 'org.apache.storm.flux.wrappers.spouts.FluxShellSpout'
            shell_object = spec.component_object.shell
            flux_dict['constructorArgs'].append([shell_object.execution_command,
                                                 shell_object.script])
            if not spec.outputs:
                flux_dict['constructorArgs'].append(['NONE_BUT_FLUX_WANTS_SOMETHING_HERE'])
            for output_stream in spec.outputs.keys():
                if output_stream == 'default':
                    output_fields = spec.outputs['default'].output_fields
                    flux_dict['constructorArgs'].append(output_fields)
                else:
                    if 'configMethods' not in flux_dict:
                        flux_dict['configMethods'] = []
                    flux_dict['configMethods'].append({
                        'name': 'setNamedStream',
                        'args': [
                            output_stream,
                            spec.outputs[output_stream].output_fields
                        ]
                    })
        else:
            if spec.component_object.serialized_java is not None:
                raise TypeError('Flux does not support specifying serialized '
                                'Java objects.  Given: {!r}'.format(spec))
            java_object = spec.component_object.java_object
            flux_dict['className'] = java_object.full_class_name
            # Convert JavaObjectArg instances into basic data types
            flux_dict['constructorArgs'] = to_python_arg_list(java_object.args_list)
        return flux_dict

    @staticmethod
    def _stream_to_flux_dict(spec, global_stream, grouping):
        """Convert a GlobalStreamId into a dict as expected by Flux"""
        flux_dict = {'from': global_stream.componentId,
                     'to': spec.name}
        grouping_dict = {'streamId': global_stream.streamId}
        for key, val in grouping.__dict__.items():
            if val is not None:
                grouping_dict['type'] = key.upper()
                if key == 'fields':
                    if val:
                        grouping_dict['args'] = val
                    else:
                        grouping_dict['type'] = 'GLOBAL'
                elif key == 'custom_object':
                    grouping_dict['type'] = 'CUSTOM'
                    class_dict = {'className': val.full_class_name,
                                  'args': to_python_arg_list(val.arg_list)}
                    grouping_dict['customClass'] = class_dict
        flux_dict['grouping'] = grouping_dict
        return flux_dict

    @classmethod
    def to_flux_dict(cls, name):
        """Convert topology to dict that can written out as Flux YAML file."""
        flux_dict = {'name': name,
                     'bolts': [],
                     'spouts': [],
                     'streams': []}
        for spec in cls.specs:
            if isinstance(spec, (JavaBoltSpec, ShellBoltSpec)):
                flux_dict['bolts'].append(cls._spec_to_flux_dict(spec))
                for global_stream, grouping in spec.inputs.items():
                    stream_dict = cls._stream_to_flux_dict(spec,
                                                           global_stream,
                                                           grouping)
                    flux_dict['streams'].append(stream_dict)
            elif isinstance(spec, (JavaSpoutSpec, ShellSpoutSpec)):
                flux_dict['spouts'].append(cls._spec_to_flux_dict(spec))
            else:
                raise TypeError('Specifications should either be bolts or '
                                'spouts.  Given: {!r}'.format(spec))
        flux_dict = {key: val for key, val in flux_dict.items() if val}
        return flux_dict

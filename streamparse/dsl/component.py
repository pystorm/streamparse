"""
Component-level Specification

This module is called component to mirror organization of pystorm package.
"""
from __future__ import absolute_import

from copy import deepcopy

import simplejson as json
from six import string_types

from ..thrift import storm_thrift
from .stream import Grouping, Stream
from .util import to_java_arg
from storm_thrift import (ComponentCommon, ComponentObject, GlobalStreamId,
                          JavaObject, ShellComponent, StreamInfo)


class ComponentSpec(object):
    """Describes the inputs, outputs, etc. for a Storm topology component.

    Generates some of the Thrift data structures that are needed to build a
    Storm topology.
    """
    def __init__(self, component_cls, name=None, inputs=None, par=1,
                 config=None, outputs=None):
        self.component_cls = component_cls
        self.name = name
        self.par = self._sanitize_par(component_cls, par)
        self.config = self._sanitize_config(component_cls, config)
        self.outputs = self._sanitize_outputs(component_cls, outputs)
        self.inputs = self._sanitize_inputs(inputs)
        self.common = ComponentCommon(inputs=self.inputs,
                                      streams=self.outputs,
                                      parallelism_hint=self.par,
                                      json_conf=self.config)

    @staticmethod
    def _sanitize_par(component_cls, par):
        """ Raises exceptions if `par` value is not a positive integer. """
        if par is None:
            par = component_cls.par
        if isinstance(par, dict):
            for stage, par_hint in par.items():
                if not (isinstance(stage, string_types) and isinstance(par_hint,
                                                                       int)):
                    raise TypeError("If par is a dict, it must map from "
                                    "environment names to integers specifying "
                                    "the parallelism hint for the component.\n"
                                    "Given stage: {!r}\n"
                                    "Given parallelism hint: {!r}"
                                    .format(stage, par_hint))
                elif par_hint < 1:
                    raise ValueError("Parallelism hint for stage {} must be an "
                                     "integer greater than 0. Given: {}"
                                     .format(stage, par_hint))
        elif not isinstance(par, int):
            raise TypeError("Parallelism hint must be an integer greater than "
                            "0. Given: {!r}".format(par))
        elif par < 1:
            raise ValueError("Parallelism hint must be an integer greater than "
                             "0. Given: {}".format(par))
        return par

    @staticmethod
    def _sanitize_inputs(inputs):
        if isinstance(inputs, dict):
            for key, val in inputs.items():
                if not isinstance(key, GlobalStreamId):
                    if isinstance(key, ComponentSpec):
                        inputs[key['default']] = val
                        del inputs[key]
                    else:
                        raise TypeError('If inputs is a dict, it is expected to'
                                        ' map from GlobalStreamId or '
                                        'ComponentSpec objects to Grouping '
                                        'objects.  Given key: {!r}; Given '
                                        'value: {!r}'.format(key, val))
                if not isinstance(val, storm_thrift.Grouping):
                    raise TypeError('If inputs is a dict, it is expected to map'
                                    ' from GlobalStreamId or ComponentSpec '
                                    'objects to Grouping objects.  Given key: '
                                    '{!r}; Given value: {!r}'.format(key, val))
            input_dict = inputs
        else:
            if isinstance(inputs, ComponentSpec):
                inputs = [inputs]
            if isinstance(inputs, (list, tuple)):
                input_dict = {}
                for input_spec in inputs:
                    grouping = Grouping.SHUFFLE
                    if isinstance(input_spec, ComponentSpec):
                        component_id = input_spec.name or input_spec
                        stream_id = GlobalStreamId(componentId=component_id,
                                                   streamId='default')
                        # Can only automatically determine if grouping should be
                        # direct when given a ComponentSpec.  If
                        # GlobalStreamId, we're out of luck.
                        # TODO: Document this.
                        default_stream = input_spec.common.streams.get('default')
                        if default_stream is not None and default_stream.direct:
                            grouping = Grouping.DIRECT
                    elif isinstance(input_spec, GlobalStreamId):
                        stream_id = input_spec
                    else:
                        raise TypeError('Inputs must be ComponentSpec or '
                                        'GlobalStreamId objects.  Given: {!r}'
                                        .format(input_spec))
                    input_dict[stream_id] = grouping
            elif inputs is None:
                input_dict = {}
            else:
                raise TypeError('Inputs must either be a list, dict, or None.  '
                                'Given: {!r}'.format(inputs))
        return input_dict

    @staticmethod
    def _sanitize_config(component_cls, config):
        if config is None:
            config = component_cls.config
        if isinstance(config, dict):
            config = json.dumps(config)
        elif config is None:
            config = '{}'
        else:
            raise TypeError('Config must either be a dict or None.  Given: {!r}'
                            .format(config))
        return config

    @staticmethod
    def _sanitize_outputs(component_cls, outputs):
        if outputs is None:
            outputs = component_cls.outputs
        if outputs is None:
            outputs = []
        if isinstance(outputs, (list, tuple)):
            streams = {}
            for output in outputs:
                if isinstance(output, Stream):
                    streams[output.name] = StreamInfo(output_fields=output.fields,
                                                      direct=output.direct)
                # Strings are output fields for default stream
                elif isinstance(output, string_types):
                    default = streams.setdefault('default',
                                                 StreamInfo(output_fields=[],
                                                            direct=False))
                    default.output_fields.append(output)
                else:
                    raise TypeError('Outputs must either be a list of strings '
                                    'or a list of Streams.  Invalid entry: {!r}'
                                    .format(output))
        else:
            raise TypeError('Outputs must either be a list of strings or a list'
                            ' of Streams.  Given: {!r}'.format(outputs))
        return streams

    def __getitem__(self, stream):
        if stream not in self.common.streams:
            raise KeyError('Invalid stream for {}: {!r}. Valid streams are: '
                           '{}'.format(self.name, stream,
                                       list(self.common.streams.keys())))
        # If name is None, because it hasn't been set yet, use object instead
        component_id = self.name or self
        return GlobalStreamId(componentId=component_id, streamId=stream)

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


class JavaComponentSpec(ComponentSpec):
    """ComponentSpec for JVM-based topology components."""
    def __init__(self, component_cls, name=None, serialized_java=None,
                 full_class_name=None, args_list=None, inputs=None,
                 par=None, config=None, outputs=None):
        super(JavaComponentSpec, self).__init__(component_cls,
                                                name=name, inputs=inputs,
                                                par=par, config=config,
                                                outputs=outputs)
        if serialized_java is not None:
            if isinstance(serialized_java, bytes):
                comp_object = ComponentObject(serialized_java=serialized_java)
                self.component_object = comp_object
            else:
                raise TypeError('serialized_java must be either bytes or None')
        else:
            if not full_class_name:
                raise ValueError('full_class_name is required')
            if args_list is None:
                raise TypeError('args_list must not be None')
            else:
                # Convert arguments to JavaObjectArgs
                for i, arg in enumerate(args_list):
                    args_list[i] = to_java_arg(arg)
            java_object = JavaObject(full_class_name=full_class_name,
                                     args_list=args_list)
            self.component_object = ComponentObject(java_object=java_object)


class ShellComponentSpec(ComponentSpec):
    """ComponentSpec for shell-based topology components (like Python ones)."""
    def __init__(self, component_cls, name=None, command=None, script=None,
                 inputs=None, par=1, config=None, outputs=None):
        super(ShellComponentSpec, self).__init__(component_cls,
                                                 name=name, inputs=inputs,
                                                 par=par, config=config,
                                                 outputs=outputs)
        if not command:
            raise ValueError('command is required')
        if script is None:
            raise TypeError('script must not be None.  If your command does not'
                            ' take arguments, specify the empty string for '
                            'script.')
        shell_component = ShellComponent(execution_command=command,
                                         script=script)
        self.component_object = ComponentObject(shell=shell_component)

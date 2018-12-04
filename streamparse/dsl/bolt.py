"""
Bolt Specification

This module is called bolt to mirror organization of storm package.
"""
from __future__ import absolute_import

from .component import JavaComponentSpec, ShellComponentSpec


class ShellBoltSpec(ShellComponentSpec):
    def __init__(
        self,
        component_cls,
        name=None,
        command=None,
        script=None,
        inputs=None,
        par=1,
        config=None,
        outputs=None,
    ):
        super(ShellBoltSpec, self).__init__(
            component_cls,
            name=name,
            inputs=inputs,
            par=par,
            config=config,
            outputs=outputs,
            command=command,
            script=script,
        )


class JavaBoltSpec(JavaComponentSpec):
    def __init__(
        self,
        component_cls,
        name=None,
        serialized_java=None,
        full_class_name=None,
        args_list=None,
        inputs=None,
        par=1,
        config=None,
        outputs=None,
    ):
        super(JavaBoltSpec, self).__init__(
            component_cls,
            name=name,
            serialized_java=serialized_java,
            inputs=inputs,
            par=par,
            config=config,
            outputs=outputs,
            full_class_name=full_class_name,
            args_list=args_list,
        )

"""
Spout Specification

This module is called spout to mirror organization of storm package.
"""
from __future__ import absolute_import

from .component import JavaComponentSpec, ShellComponentSpec


class ShellSpoutSpec(ShellComponentSpec):
    def __init__(
        self,
        component_cls,
        name=None,
        command=None,
        script=None,
        par=1,
        config=None,
        outputs=None,
    ):
        super(ShellSpoutSpec, self).__init__(
            component_cls,
            name=name,
            par=par,
            config=config,
            outputs=outputs,
            command=command,
            script=script,
        )


class JavaSpoutSpec(JavaComponentSpec):
    def __init__(
        self,
        component_cls,
        name=None,
        serialized_java=None,
        full_class_name=None,
        args_list=None,
        par=1,
        config=None,
        outputs=None,
    ):
        super(JavaSpoutSpec, self).__init__(
            component_cls,
            name=name,
            par=par,
            config=config,
            outputs=outputs,
            serialized_java=serialized_java,
            full_class_name=full_class_name,
            args_list=args_list,
        )

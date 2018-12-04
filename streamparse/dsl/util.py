"""
Utility functions for the DSL
"""

from __future__ import absolute_import

from six import integer_types, text_type

from ..thrift import JavaObjectArg


def to_java_arg(arg):
    """Converts Python objects to equivalent Thrift JavaObjectArgs"""
    if isinstance(arg, bool):
        java_arg = JavaObjectArg(bool_arg=arg)
    elif isinstance(arg, integer_types):
        # Just use long all the time since Python 3 doesn't
        # distinguish between long and int
        java_arg = JavaObjectArg(long_arg=arg)
    elif isinstance(arg, bytes):
        java_arg = JavaObjectArg(binary_arg=arg)
    elif isinstance(arg, text_type):
        java_arg = JavaObjectArg(string_arg=arg)
    elif isinstance(arg, float):
        java_arg = JavaObjectArg(double_arg=arg)
    else:
        raise TypeError(
            "Only basic data types can be specified"
            " as arguments to JavaObject "
            "constructors.  Given: {!r}".format(arg)
        )
    return java_arg


def to_python_arg(java_arg):
    """Convert a Thrift JavaObjectArg into a basic Python data type"""
    arg = None
    for val in java_arg.__dict__.values():
        if val is not None:
            arg = val
            break
    return arg


def to_python_arg_list(java_arg_list):
    """Convert a list of Thrift JavaObjectArg objects into a list of basic types"""
    return [to_python_arg(java_arg) for java_arg in java_arg_list]

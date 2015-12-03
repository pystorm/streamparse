"""
Utility functions for the DSL
"""

from __future__ import absolute_import

from six import text_type

from ..thrift import storm_thrift


def to_java_arg(arg):
    """Converts Python objects to equivalent Thrift JavaObjectArgs"""
    if isinstance(arg, bool):
        return storm_thrift.JavaObjectArg(bool_arg=arg)
    elif isinstance(arg, int):
        return storm_thrift.JavaObjectArg(long_arg=arg)
    elif isinstance(arg, bytes):
        return storm_thrift.JavaObjectArg(binary_arg=arg)
    elif isinstance(arg, text_type):
        return storm_thrift.JavaObjectArg(string=arg)
    elif isinstance(arg, float):
        return storm_thrift.JavaObjectArg(double_arg=arg)
    else:
        return TypeError('arg is not a valid type to pass to Java: {!r}'
                         .format(arg))

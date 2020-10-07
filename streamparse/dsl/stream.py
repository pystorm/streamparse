"""
Streams and Groupings
"""
from ..thrift import JavaObject, NullStruct, storm_thrift, StreamInfo
from .util import to_java_arg


class Stream(StreamInfo):
    """
    A Storm output stream
    """

    def __init__(self, fields=None, name="default", direct=False):
        """
        :param fields: Field names for this stream.
        :type fields:  `list` or `tuple` of `str`
        :param name:   Name of stream.  Defaults to ``default``.
        :type name:    `str`
        :param direct: Whether or not this stream is direct.  Default is `False`.
                       See :attr:`~streamparse.dsl.stream.Grouping.DIRECT`.
        :type direct:  `bool`
        """
        if fields is None:
            fields = []
        elif isinstance(fields, (list, tuple)):
            fields = list(fields)
            for field in fields:
                if not isinstance(field, str):
                    raise TypeError(
                        f"All field names must be strings; given: {field!r}"
                    )
        else:
            raise TypeError(
                f"Stream fields must be a list, tuple, or None; given: {fields!r}"
            )
        self.fields = fields
        if isinstance(name, str):
            self.name = name
        else:
            raise TypeError(f"Stream name must be a string; given: {name!r}")
        if isinstance(direct, bool):
            self.direct = direct
        else:
            raise TypeError(
                f'"direct" must be either True or False; given: {direct!r}'
            )


class _Grouping(storm_thrift.Grouping):
    """
    Version of `storm_thrift.Grouping` that has better __str__.
    """

    def __repr__(self):
        for name, val in vars(self).items():
            if not name.startswith("_") and val is not None:
                if isinstance(val, NullStruct):
                    return f"{name.upper()}"
                else:
                    return f"{name}({val!r})"


class Grouping:
    """
    A Grouping describes how Tuples should be distributed to the tasks of a
    Bolt listening on a particular stream.

    When no Grouping is specified, it defaults to `SHUFFLE` for normal streams,
    and `DIRECT` for direct streams.

    :ivar SHUFFLE: Tuples are randomly distributed across the Bolt's tasks in a
                   way such that each Bolt is guaranteed to get an equal number
                   of Tuples.
    :ivar GLOBAL: The entire stream goes to a single one of the Bolt's tasks.
                  Specifically, it goes to the task with the lowest id.
    :ivar DIRECT: This is a special kind of grouping. A stream grouped this way
                  means that the producer of the Tuple decides which task of the
                  consumer will receive this Tuple. Direct groupings can only be
                  declared on streams that have been declared as direct streams.
                  Tuples emitted to a direct stream must be emitted using the
                  the `direct_task` parameter to the
                  :meth:`streamparse.Bolt.emit` and
                  :meth:`streamparse.Spout.emit` methods.
    :ivar ALL: The stream is replicated across all the Bolt's tasks. Use this
               grouping with care.
    :ivar NONE: This grouping specifies that you don't care how the stream is
                grouped. Currently, none groupings are equivalent to shuffle
                groupings. Eventually though, Storm will push down Bolts with
                none groupings to execute in the same thread as the Bolt or
                Spout they subscribe from (when possible).
    :ivar LOCAL_OR_SHUFFLE: If the target Bolt has one or more tasks in the
                            same worker process, Tuples will be shuffled to
                            just those in-process tasks. Otherwise, this acts
                            like a normal shuffle grouping.
    """

    __slots__ = ()

    SHUFFLE = _Grouping(shuffle=NullStruct())
    GLOBAL = _Grouping(fields=[])
    DIRECT = _Grouping(direct=NullStruct())
    ALL = _Grouping(all=NullStruct())
    NONE = _Grouping(none=NullStruct())
    LOCAL_OR_SHUFFLE = _Grouping(local_or_shuffle=NullStruct())

    @classmethod
    def fields(cls, *fields):
        """The stream is partitioned by the fields specified in the grouping.

        For example, if the stream is grouped by the `user-id` field, Tuples
        with the same `user-id` will always go to the same task, but Tuples with
        different `user-id`'s may go to different tasks."""
        if len(fields) == 1 and isinstance(fields[0], list):
            fields = fields[0]
        else:
            fields = list(fields)
        if not fields:
            raise ValueError("List cannot be empty for fields grouping")
        return _Grouping(fields=fields)

    @classmethod
    def custom_object(cls, java_class_name, arg_list):
        """Tuples will be assigned to tasks by the given Java class."""
        java_object = JavaObject(
            full_class_name=java_class_name,
            args_list=[to_java_arg(arg) for arg in arg_list],
        )
        return _Grouping(custom_object=java_object)

    @classmethod
    def custom_serialized(cls, java_serialized):
        """Tuples will be assigned to tasks by the given Java serialized class."""
        if not isinstance(java_serialized, bytes):
            return TypeError(
                "Argument to custom_serialized must be a "
                "serialized Java class as bytes.  Given: {!r}".format(java_serialized)
            )
        return _Grouping(custom_serialized=java_serialized)

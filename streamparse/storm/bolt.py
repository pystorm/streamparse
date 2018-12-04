"""
Module to add streamparse-specific extensions to pystorm Bolt classes
"""

import pystorm

from ..dsl.bolt import JavaBoltSpec, ShellBoltSpec
from .component import Component


class JavaBolt(Component):
    @classmethod
    def spec(
        cls,
        name=None,
        serialized_java=None,
        full_class_name=None,
        args_list=None,
        inputs=None,
        par=1,
        config=None,
        outputs=None,
    ):
        """Create a :class:`JavaBoltSpec` for a Java Bolt.

        This spec represents this Bolt in a :class:`~streamparse.Topology`.

        You must add the appropriate entries to your classpath by editing your
        project's ``project.clj`` file in order for this to work.

        :param name:   Name of this Bolt.  Defaults to name of
                       :class:`~streamparse.Topology` attribute this is assigned
                       to.
        :type name:    `str`
        :param serialized_java:  Serialized Java code representing the class.
                                 You must either specify this, or
                                 both ``full_class_name`` and ``args_list``.
        :type serialized_java: `bytes`
        :param full_class_name: Fully qualified class name (including the
                                package name)
        :type full_class_name: `str`
        :param args_list: A list of arguments to be passed to the constructor of
                          this class.
        :type args_list: `list` of basic data types
        :param inputs: Streams that feed into this Bolt.

                       Two forms of this are acceptable:

                       1.  A `dict` mapping from
                           :class:`~streamparse.dsl.component.ComponentSpec` to
                           :class:`~streamparse.Grouping`.
                       2.  A `list` of :class:`~streamparse.Stream` or
                           :class:`~streamparse.dsl.component.ComponentSpec`.
        :param par:    Parallelism hint for this Bolt.  For Python
                       Components, this works out to be the number of Python
                       processes running it in the the topology (across all
                       machines).  See :ref:`parallelism`.
        :type par:     `int`
        :param config: Component-specific config settings to pass to Storm.
        :type config:  `dict`
        :param outputs: Outputs this JavaBolt will produce. Acceptable forms
                        are:

                        1.  A `list` of :class:`~streamparse.Stream` objects
                            describing the fields output on each stream.
                        2.  A `list` of `str` representing the fields output on
                            the ``default`` stream.
        """
        return JavaBoltSpec(
            cls,
            name=name,
            serialized_java=serialized_java,
            full_class_name=full_class_name,
            args_list=args_list,
            inputs=inputs,
            par=par,
            config=config,
            outputs=outputs,
        )


class ShellBolt(Component):
    """A Bolt that is started by running a command with a script argument."""

    @classmethod
    def spec(
        cls,
        name=None,
        command=None,
        script=None,
        inputs=None,
        par=None,
        config=None,
        outputs=None,
    ):
        """Create a :class:`ShellBoltSpec` for a non-Java, non-Python Bolt.

        If you want to create a spec for a Python Bolt, use
        :meth:`~streamparse.dsl.bolt.Bolt.spec`.

        This spec represents this Bolt in a :class:`~streamparse.Topology`.

        :param name:   Name of this Bolt.  Defaults to name of
                       :class:`~streamparse.Topology` attribute this is assigned
                       to.
        :type name:    `str`
        :param command:  Path to command the Storm will execute.
        :type command: `str`
        :param script: Arguments to `command`.  Multiple arguments should just
                       be separated by spaces.
        :type script: `str`
        :param inputs: Streams that feed into this Bolt.

                       Two forms of this are acceptable:

                       1.  A `dict` mapping from
                           :class:`~streamparse.dsl.component.ComponentSpec` to
                           :class:`~streamparse.Grouping`.
                       2.  A `list` of :class:`~streamparse.Stream` or
                           :class:`~streamparse.dsl.component.ComponentSpec`.
        :param par:    Parallelism hint for this Bolt.  For shell
                       Components, this works out to be the number of running it
                       in the the topology (across all machines).
                       See :ref:`parallelism`.
        :type par:     `int`
        :param config: Component-specific config settings to pass to Storm.
        :type config:  `dict`
        :param outputs: Outputs this ShellBolt will produce. Acceptable forms
                        are:

                        1.  A `list` of :class:`~streamparse.Stream` objects
                            describing the fields output on each stream.
                        2.  A `list` of `str` representing the fields output on
                            the ``default`` stream.
        """
        return ShellBoltSpec(
            cls,
            command=command,
            script=script,
            name=name,
            inputs=inputs,
            par=par,
            config=config,
            outputs=outputs,
        )


class Bolt(pystorm.bolt.Bolt, ShellBolt):
    """pystorm Bolt with streamparse-specific additions"""

    @classmethod
    def spec(cls, name=None, inputs=None, par=None, config=None):
        """Create a :class:`~ShellBoltSpec` for a Python Bolt.

        This spec represents this Bolt in a :class:`~streamparse.Topology`.

        :param name:   Name of this Bolt.  Defaults to name of
                       :class:`~streamparse.Topology` attribute this is assigned
                       to.
        :type name:    `str`
        :param inputs: Streams that feed into this Bolt.

                       Two forms of this are acceptable:

                       1.  A `dict` mapping from
                           :class:`~streamparse.dsl.component.ComponentSpec` to
                           :class:`~streamparse.Grouping`.
                       2.  A `list` of :class:`~streamparse.Stream` or
                           :class:`~streamparse.dsl.component.ComponentSpec`.
        :param par:    Parallelism hint for this Bolt.  For Python
                       Components, this works out to be the number of Python
                       processes running it in the the topology (across all
                       machines).  See :ref:`parallelism`.

                       .. note::
                           This can also be specified as an attribute of your
                           :class:`~Bolt` subclass.

        :type par:     `int`
        :param config: Component-specific config settings to pass to Storm.

                       .. note::
                           This can also be specified as an attribute of your
                           :class:`~Bolt` subclass.

        :type config:  `dict`

        .. note::
            This method does not take a ``outputs`` argument because
            ``outputs`` should be an attribute of your :class:`~Bolt` subclass.
        """
        return ShellBoltSpec(
            cls,
            command="streamparse_run",
            script="{}.{}".format(cls.__module__, cls.__name__),
            name=name,
            inputs=inputs,
            par=par,
            config=config,
            outputs=cls.outputs,
        )


class BatchingBolt(pystorm.bolt.BatchingBolt, Bolt):
    """pystorm BatchingBolt with streamparse-specific additions"""

    pass


class TicklessBatchingBolt(pystorm.bolt.TicklessBatchingBolt, BatchingBolt):
    """pystorm TicklessBatchingBolt with streamparse-specific additions"""

    pass

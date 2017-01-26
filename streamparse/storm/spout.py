"""
Module to add streamparse-specific extensions to pystorm Spout class
"""

import pystorm

from ..dsl.spout import JavaSpoutSpec, ShellSpoutSpec
from .component import Component


class JavaSpout(Component):
    @classmethod
    def spec(cls, name=None, serialized_java=None, full_class_name=None,
             args_list=None, par=1, config=None, outputs=None):
        """Create a :class:`JavaSpoutSpec` for a Java Spout.

        This spec represents this Spout in a :class:`~streamparse.Topology`.

        You must add the appropriate entries to your classpath by editing your
        project's ``project.clj`` file in order for this to work.

        :param name:   Name of this Spout.  Defaults to name of
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
        :param par:    Parallelism hint for this Spout. See :ref:`parallelism`.
        :type par:     `int`
        :param config: Component-specific config settings to pass to Storm.
        :type config:  `dict`
        :param outputs: Outputs this JavaSpout will produce. Acceptable forms
                        are:

                        1.  A `list` of :class:`~streamparse.Stream` objects
                            describing the fields output on each stream.
                        2.  A `list` of `str` representing the fields output on
                            the ``default`` stream.
        """
        return JavaSpoutSpec(cls, name=name, serialized_java=serialized_java,
                             full_class_name=full_class_name,
                             args_list=args_list, par=par,
                             config=config, outputs=outputs)


class ShellSpout(Component):
    @classmethod
    def spec(cls, name=None, command=None, script=None, par=None, config=None,
             outputs=None):
        """Create a :class:`ShellSpoutSpec` for a non-Java, non-Python Spout.

        If you want to create a spec for a Python Spout, use
        :meth:`~streamparse.dsl.bolt.Spout.spec`.

        This spec represents this Spout in a :class:`~streamparse.Topology`.

        :param name:   Name of this Spout.  Defaults to name of
                       :class:`~streamparse.Topology` attribute this is assigned
                       to.
        :type name:    `str`
        :param command:  Path to command the Storm will execute.
        :type command: `str`
        :param script: Arguments to `command`.  Multiple arguments should just
                       be separated by spaces.
        :type script: `str`
        :param par:    Parallelism hint for this Spout.  For shell
                       Components, this works out to be the number of processes
                       running it in the the topology (across all machines).
                       See :ref:`parallelism`.
        :type par:     `int`
        :param config: Component-specific config settings to pass to Storm.
        :type config:  `dict`
        :param outputs: Outputs this ShellSpout will produce. Acceptable forms
                        are:

                        1.  A `list` of :class:`~streamparse.Stream` objects
                            describing the fields output on each stream.
                        2.  A `list` of `str` representing the fields output on
                            the ``default`` stream.
        """
        return ShellSpoutSpec(cls, command=command, script=script, name=name,
                              par=par, config=config, outputs=outputs)


class Spout(pystorm.spout.Spout, ShellSpout):
    """pystorm Spout with streamparse-specific additions"""
    @classmethod
    def spec(cls, name=None, par=None, config=None):
        """Create a :class:`~ShellBoltSpec` for a Python Spout.

        This spec represents this Spout in a :class:`~streamparse.Topology`.

        :param name:   Name of this Spout.  Defaults to name of
                       :class:`~streamparse.Topology` attribute this is assigned
                       to.
        :type name:    `str`
        :param par:    Parallelism hint for this Spout.  For Python
                       Components, this works out to be the number of Python
                       processes running it in the the topology (across all
                       machines).  See :ref:`parallelism`.

                       .. note::
                           This can also be specified as an attribute of your
                           :class:`~Spout` subclass.

        :type par:     `int`
        :param config: Component-specific config settings to pass to Storm.

                       .. note::
                           This can also be specified as an attribute of your
                           :class:`~Spout` subclass.

        :type config:  `dict`

        .. note::
            This method does not take a ``outputs`` argument because
            ``outputs`` should be an attribute of your :class:`~Spout` subclass.
        """
        return ShellSpoutSpec(cls, command='streamparse_run',
                              script='{}.{}'.format(cls.__module__,
                                                    cls.__name__),
                              name=name, par=par, config=config,
                              outputs=cls.outputs)


class ReliableSpout(pystorm.spout.ReliableSpout, Spout):
    """pystorm ReliableSpout with streamparse-specific additions"""
    pass

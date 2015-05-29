"""
Topology base class
"""
from six import add_metaclass, iteritems

from .component import Specification


class Grouping(object):
    SHUFFLE = ":shuffle"
    GLOBAL = ":global"
    DIRECT = ":direct"
    ALL = ":all"

    @classmethod
    def fields(cls, *fieldlist):
        return list(fieldlist)

    @classmethod
    def valid(cls, grouping):
        return (
            isinstance(grouping, list) or
            grouping in (
                Grouping.SHUFFLE,
                Grouping.GLOBAL,
                Grouping.DIRECT,
                Grouping.ALL,
            )
        )


class TopologyType(type):
    def __new__(meta, classname, bases, class_dict):
        specs = {}
        for name, spec in iteritems(class_dict):
            if isinstance(spec, Specification):

                # Use the variable name as the specification name.
                if spec.name is None:
                    spec.name = name

                if spec.name not in specs:
                    specs[spec.name] = spec
                else:
                    raise TopologyError(
                        "Duplicate specification name: {}".format(spec.name))

        class_dict["specs"] = specs.values()

        # Resolve dependencies in specifications.
        for name, spec in iteritems(specs):
            spec.resolve_dependencies(specs)

        return type.__new__(meta, classname, bases, class_dict)


@add_metaclass(TopologyType)
class Topology(object):
    pass


class TopologyError(Exception):
    pass

"""
Topology base class
"""
from ..storm.spout import Spout
from ..storm.bolt import Bolt


class Spec(object):
    def __init__(
        self,
        component,
        name=None,
        parallelism=1,
        source=None,
        group_on=None,
    ):
        self.cls = component
        self.name = name
        self.parallelism = parallelism
        self.source = source
        self.group_on = group_on


class Grouping(object):
    SHUFFLE = ":shuffle"
    GLOBAL = ":global"
    DIRECT = ":direct"
    ALL = ":all"

    @classmethod
    def fields(cls, *fieldlist):
        return list(fieldlist)


class TopologyType(type):
    def __new__(meta, classname, bases, class_dict):
        specs = []
        for name, value in class_dict.iteritems():
            if isinstance(value, Spec):
                if value.name is None:
                    value.name = name
                specs.append(value)
        class_dict["specs"] = specs
        return type.__new__(meta, classname, bases, class_dict)


class Topology(object):
    __metaclass__ = TopologyType

    @classmethod
    def _verify(cls):
        for spec in cls.specs:
            if issubclass(spec.cls, Spout):
                if spec.source is not None:
                    raise ValueError("Spouts cannot have sources")
            elif issubclass(spec.cls, Bolt):
                if spec.source is None:
                    raise ValueError("Bolts requires at least one source")
            else:
                raise TypeError("Unknown spec: {}".format(spec.cls))

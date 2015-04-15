from ..storm.spout import Spout, SpoutSpecification
from ..storm.bolt import Bolt, BoltSpecification


def Spec(component_cls, *args, **kwargs):
    """A Specification factory that allows Topologies to be defined via
    Spec(Specification, ...)
    """
    if issubclass(component_cls, Spout):
        return SpoutSpecification(component_cls, *args, **kwargs)
    elif issubclass(component_cls, Bolt):
        return BoltSpecification(component_cls, *args, **kwargs)
    else:
        raise TypeError("Unhandled component: {}".format(component_cls))

"""
Topology base class
"""

class ComponentSpec(dict):
  pass

class FieldListMeta(type):
    def __new__(meta, classname, bases, class_dict):
        field_list = []
        some_class = ComponentSpec
        for name, value in class_dict.iteritems():
            if isinstance(value, ComponentSpec):
                value.setdefault("name", name)
                field_list.append(value)
        class_dict["field_list"] = field_list
        return type.__new__(meta, classname, bases, class_dict)

class Topology(object):
  __metaclass__ = FieldListMeta


import collections


def merge_dicts(a, b):
    for k, v in b.items():
        if k in a and isinstance(a[k], dict) and isinstance(b[k], collections.Mapping):
            merge_dicts(a[k], b[k])
        else:
            a[k] = b[k]


def dict_property(name, modifier=None):
    if modifier is None:
        def getter(self):
            return self[name]
    else:
        def getter(self):
            return modifier(self[name])

    def setter(self, value):
        if value is not None:
            self[name] = value

    return property(getter, setter)


def dict_array_property(name, modifier=None):
    if modifier is None:
        def getter(self):
            return self[name]
    else:
        def getter(self):
            for item in self[name]:
                yield modifier(item)

    def setter(self, value):
        if value is not None:
            self[name] = value

    return property(getter, setter)
# -*- coding: utf-8 -*-


class ConfigOrmHandler(object):
    def __init__(self, base_class, mapping=None):

        if mapping is None:
            mapping = {}

        self._mapping = mapping
        self._base_class = base_class

    def add(self, key, mapped_class):

        self._mapping[key] = mapped_class

    def get(self, key):

        if key and key in self._mapping:
            ORMClass = type(self._base_class.__name__, (self._mapping[key], self._base_class), {})
        else:
            ORMClass = self._base_class

        return ORMClass

# -*- coding: utf-8 -*-

from twisted.logger import Logger

logging = Logger()


class ConfigOrmHandler(object):

    def __init__(self, baseclass, mapping=None):

        self._mapping = mapping or {}
        self._baseclass = baseclass

    def add(self, key, mapped_class):

        self._mapping[key] = mapped_class

    def get(self, key):

        if key and key in self._mapping:
            orm_class = type(
                self._baseclass.__name__,
                (self._mapping[key], self._baseclass), {})
        else:
            orm_class = self._baseclass

        return orm_class
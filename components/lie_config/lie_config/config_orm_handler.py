# -*- coding: utf-8 -*-

from twisted.logger  import Logger

logging = Logger()

class ConfigOrmHandler(object):
    
    def __init__(self, baseclass, mapping={}):
        
        self._mapping = mapping
        self._baseclass = baseclass
    
    def add(self, key, mapped_class):
        
        self._mapping[key] = mapped_class
    
    def get(self, key):
        
        if key and key in self._mapping:
            ORMClass = type(self._baseclass.__name__, (self._mapping[key], self._baseclass), {})
        else:
            ORMClass = self._baseclass
        
        return ORMClass
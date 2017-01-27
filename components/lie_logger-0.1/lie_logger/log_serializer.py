# -*- coding: utf-8 -*-

from __future__ import unicode_literals

class LogSerializer(object):
    """
    Simple structured log serializer.
    
    Serializes a log dictionary for storage in for instance a MongoDB database.
    Supports serialization of Python primitive types and will replace 
    non-serializble object with the `nonserial` argument.
    
    By default, `serial_replace` is set to None which will result in the object
    being removed from the log dictionary. This operates in a cumultative fasion:
    if all objects in a list are not serializable, the list itself will be
    removed even though a list is a primitive type.
    `serial_replace` may be a callable function.
    
    The serializer supports serialization upto a certain depth for nested 
    log dictionaries.
    
    .. note:: All strings are converted to unicode using unicode_literals from
              the __future__ package (python 2, native in python 3).
    
    :param max_depth:      maximum object depth to serialize
    :type max_depth:       int
    :param serial_replace: attribute to replace non-serializble object with
    :type serial_replace:  mixed 
    """
    
    def __init__(self, max_depth=1, serial_replace=None):
        
        self.max_depth = max_depth
        self.serial_replace = serial_replace
        
        self.non_iterable_primitives = [str, int, float, bool, unicode]
        self.non_keyword_iterable_primitives = [list, set]
        self.keyword_iterable_primitives = [dict]
    
    def _serialize_list(self, obj, depth):
        """
        Serialize a non-keyword based iterable object
        
        :param obj:   object to serialize
        :type obj:    mixed
        :param depth: current object depth
        :type depth:  int
        """
        
        f = []
        for v in obj:
            v = self._iter_serialize(v, depth=depth+1)
            if v == None:
                continue
            f.append(v)
        
        if len(f):
            return f
    
    def _serialize_dict(self, obj, depth):
        """
        Serialize a keyword based iterable object
        
        :param obj:   object to serialize
        :type obj:    mixed
        :param depth: current object depth
        :type depth:  int
        """
        
        f = {}
        for k,v in obj.items():
            v = self._iter_serialize(v, depth=depth+1)
            if v == None:
                continue
            f[k] = v
        
        if len(f):
            return f
          
    def _iter_serialize(self, obj, depth=0):
        """
        Iteratively serialize a nested object in which each
        Python primitive type group is processed separately.
        
        :param obj:   nested object to serialize
        :type obj:    mixed
        :param depth: current object depth
        :type depth:  int
        """
        
        # Stop processing when reaching max_depth
        if depth > self.max_depth:
            return 
        
        object_type = type(obj)
        serialized = None
        
        # Process non iterable primitive types
        if object_type in self.non_iterable_primitives:
            serialized = obj
        
        # Process dictionaries
        if object_type in self.keyword_iterable_primitives:
            serialized = self._serialize_dict(obj, depth)
        
        # Process lists and sets
        if object_type in self.non_keyword_iterable_primitives:
            serialized = self._serialize_list(obj, depth)
        
        # Returned serialized or non-serializable replacement
        if serialized != None:
            return serialized
        if callable(self.serial_replace):
            return self.serial_replace(obj)
        return self.serial_replace
    
    def encode(self, obj):
        """
        Base method for encoding (serializing) a log dictionary
        
        :param obj: log dictionary to serialize
        :type obj:  :py:dict
        """
        
        serialized = {}
        serialized.update(self._iter_serialize(obj))
        
        return serialized

if __name__ == '__main__':
    
    import time
    
    class h(object):
        
        opp=2
    
    d = {'user':'marc', 'age':39, 'flags':['one',2, u"three"], "time":time.time(), 'class':h(), 'dict':{'one':1, 2:'two', 3:h()}}
    
    ser = LogSerializer(max_depth=1)
    l = ser.encode(d)
    print(l)
#!/usr/bin/env python

import re
import copy
import logging
import weakref

from   fnmatch        import fnmatch
from   twisted.logger import Logger

from   .config_format import ConfigFormatter
from   .config_io     import _flatten_nested_dict

logging = Logger()

class DictWrapper(dict):
    pass

class ConfigHandler(object):
  """
  
  TODO: harmonize difference in dictionary methods between Python 2.x and 3.x
        Perhaps inherit from 2.x, 3.x specific dict method class.
  TODO: __getitem__ and get for multiple keys at once
  """          
  
  def __init__(self, config={}, keys=None, freeze=False, format_value=ConfigFormatter, level=0):
    """
    Implement class __init__ method
    
    :param freeze:       allow addition of new keys or removal of keys
    :type freeze:        bool
    :param format_value: parse the value through the custom ConfigFormatter string
                         formatting class before returning
    :type format_value:  bool
    """
    
    # If this is the root instance of the config dict
    # setup a weak reference to it.
    if not isinstance(config, DictWrapper):
      wrapped_config = DictWrapper(config)
      self.config = weakref.ref(wrapped_config)()
    else:
      self.config = config
    
    # Instantiate format class if needed
    if type(format_value).__name__ == 'type':
      self.format_value = format_value(self)
    else:
      self.format_value = format_value
    
    self.level  = level
    self.freeze = freeze
    
    self._keys  = {}
    self._reskeys = keys
    self._resolve_config_level(self._reskeys)
    self._initialised = True
    
  def __call__(self):
    """
    Implement class __call__ method
    
    .. note:: This function will return a copy of the (sub)dictionary
              the object represents.
    
    :return: full configuration dictionary
    :rtype:  dict
    """
    
    return self._leveled_dict_copy()
  
  def __deepcopy__(self, memo={}):
    """
    Deepcopy directives for this class
    
    All __dict__ attributes except the config dictionary
    are deepcopied.
    For the config dictionary a copy is made for only
    those keys that reflect the (sub)dictionary of the
    class instance.
    """
    
    new = ConfigHandler.__new__(ConfigHandler) 
    memo[id(self)] = new
    
    for n, v in self.__dict__.items():
      if not n == 'config':
        setattr(new, n, copy.deepcopy(v, memo)) 
    new.config = self.dict()
    
    return new
  
  def __contains__(self, key):
    """
    Implement class __contains__ method
    
    :return: if the dictionary contains the key
    :rtype:  bool
    """
    
    for k in self._keys:
      if k.startswith(key):
        return True
    
    return False
    
  def __eq__(self, other):
    
    if isinstance(other, ConfigHandler):
      return self.keys() == other.keys()
    
  def __ne__(self, other):
    
    if isinstance(other, ConfigHandler):
      return self.keys() != other.keys()
  
  def __lt__(self, other):
    
    if isinstance(other, ConfigHandler):
      return len(self) < len(other)
  
  def __gt__(self, other):
    
    if isinstance(other, ConfigHandler):
      return len(self) > len(other)
  
  def __le__(self, other):
    
    if isinstance(other, ConfigHandler):
      return len(self) <= len(other)
  
  def __ge__(self, other):
    
    if isinstance(other, ConfigHandler):
      return len(self) >= len(other)
   
  def __add__(self, other):
    """
    Implements addition.
    
    Add (sub)dictionary keys from other to self.
    Check if corresponding other.config key,value
    pairs are in self.config and add if needed.
    
    :param other: other ConfigHandler instance
    :type other:  ConfigHandler instance
    """
    
    self.update(other)
  
  def __sub__(self, other):
    """
    Implements subtraction.
    
    Subtract (sub)dictionary keys of other from
    self. Does not remove key,value pairs in
    self.config.
    
    :param other: other ConfigHandler instance
    :type other:  ConfigHandler instance
    """
    
    if isinstance(other, ConfigHandler):
      sub_count = 0
      for k,v in other._keys.items():
        if k in self._keys:
          self._keys.remove(k)
          sub_count += 1
  
  __radd__ = __add__
  __rsub__ = __sub__
  __iadd__ = __add__
  __isub__ = __sub__
  
  def __delattr__(self, key):
    
    self.remove(key)
  
  __delitem__ = __delattr__
    
  def __getattr__(self, key):
    """
    __getattr__ overload.
    
    Expose dictionary keys as class attributes.
    fallback to the default __getattr__ behaviour.
    Returns subdictionaries from root to leafs for nested dictionaries
    similar to the default dict behaviour.

    :param name: attribute name
    :return:     subdirectory for nested keys, value for unique keys.
    """
    
    if not key in self.__dict__:
      if key in self._keys:
        return self.get(key)

      query = self.search('^{0}(?=.|$)'.format(key), regex=True, level=self.level+1)
      if len(query) == 1 and key in query.keys():
        return query.get(key)
      if len(query):
        return query
    
    return object.__getattribute__(self, key)
    
  def __getitem__(self, key):
    """
    __getitem__ overload.
    
    Get values using dictionary style access, fallback to default __getitem__
    Returns subdictionaries from root to leafs for nested dictionaries
    similar to the default dict behaviour.
    
    __getitem__ uses the `search` method to find matching keys using the 
    regular expression '^seach_key(?=.|$)'. Key has to be at the beginning of
    the string followed by a dot '.' or nothing (end of string).
    Other regular expressions or Unix style wildcard matches are not supported.

    :param name: attribute name
    :type name:  str
    :return:     subdirectory for nested keys, value for unique keys.
    """
    
    if not key in self.__dict__:
      
      query = self.search('^{0}(?=.|$)'.format(key), regex=True, level=self.level+1)
      if len(query) == 1 and key in query._keys.values():
        return query.get(list(query._keys)[0])
      if len(query) == 1 and key in query._keys.keys():
        return query.get(key)
      if len(query):
        return query
      
    return self.__dict__[key]
  
  def __iter__(self):
    """
    Implement class __iter__ method
    
    Iterate over first level keys this (sub)dictionary represents
    
    :return: dictionary keys
    :rtype:  generator object
    """
    
    for key in self.get_attributes_at_level():
      yield key
    
  def __len__(self):
    """
    Implement class __len__ method
 
    :return: number of dictionary entries
    :rtype:  int
    """
    
    return len(self._keys)
  
  def __nonzero__(self):
    
    return len(self._keys) != 0
  
  __bool__ = __nonzero__
    
  def __repr__(self):
    """
    Implement class __repr__ method
 
    :return: class instance information
    :rtype:  str
    """
    
    return '<{0} object {1}: {2} parameters, level {3}>'.format(self.__class__.__name__, 
      id(self), len(self._keys), self.level)
  
  def __setattr__(self, key, value):
    """
    __setattr__ overload.
    
    Set dictionary entries using class attribute setter methods
    fallback to the default __setattr__ behaviour.

    :param name:  attribute name.
    :param value: attribute value
    """
    
    if not '_initialised' in self.__dict__:
      return dict.__setattr__(self, key, value)
    elif key in self._keys:
      self.set(key, value)
    else:
      self.__setitem__(key, value)
  
  def __setitem__(self, key, value):
    """
    __setitem__ overload.
    
    Set values using dictionary style access, fallback to
    default __setattr__

    :param key:   attribute name
    :type key:    str
    :param value: attribute value
    """  
    
    if key in self._keys:
      self.set(key, value)
    else:
      dict.__setattr__(self, key, value)
  
  def __str__(self):
    """
    Implement class __str__ method.
    
    :return: print friendly overview of settings
    :rtype:  str
    """
    
    overview = []
    for k in sorted(self._keys.keys()):
      overview.append('{0}: {1}\n'.format(k,self.config[self._keys[k]]))
    
    return ''.join(overview)
    
  def _resolve_config_level(self, keys=None):
    """
    Set the keys in self._keys to reflect the attribute level
    in a nested dictionary and resolve attribute order when
    overloading similar attributes.
    """
    
    for key in keys or self.config.keys():
      splitted = key.split('.')
      if self.level >= len(splitted):
        self._keys[splitted[-1]] = key
      else:
        self._keys['.'.join(splitted[self.level:])] = key
  
  def _leveled_dict_copy(self):
    
    return dict([ (key,self.config[value]) for key,value in self._keys.items() ])
  
  def _format(self, value):
    
    try:
      return self.format_value.format(value)
    except:
      return value
  
  def clear(self):
    """
    Clear the dictionary of all key,value pairs
    
    Do not allow clearance of key,value pairs if the 
    dictionary is freezed
    """
    
    if self.freeze:
      raise KeyError('Unable to clear freezed dictionary'.format(key))
    
    self._keys = []
    self.config.clear()
  
  def dict(self, nested=False):
    """
    Return a copy of the (nested) (sub)dictionary represented 
    by the class with formatted values.
    
    :param nested: return a nested or flat dictionary
    :type nested:  bool
    :rtype:        dict
    """
      
    if nested:
      nested_dict = {}
      for key,value in self._keys.items():
        
        splitted = key.split('.')
        d = nested_dict
        for k in splitted[:-1]:
          if not k in d:
            d[k] = {}
          d = d[k]
        
        d[splitted[-1]] = self.get(key)
    else:
      nested_dict = dict([(k,self.get(k)) for k in self._keys])
      
    return nested_dict  
      
  def flatten(self, resolve_order=None, level=1):
    """
    Flatten the (sub)dictionary at a given level set to
    the first level by default.
    
    Similar named dictionary items are over loaded either in 
    alphabetic order of the first level attribute names or
    by the order provided through the resolve_order list.
    
    :param resolve_order: attribute order for parameter over loading
    :type resolve_order:  list
    :param level:         level up to which to flatten the nested
                          dictionary. The first level by default.
    :type level:          int
    """
    
    order = self.get_attributes_at_level(0)
    if resolve_order:
      assert isinstance(resolve_order, (tuple,list)), 'resolve_order not of type list or tuple'
      order = [n for n in order if n not in resolve_order] + resolve_order
    
    flattened = {}
    for key in order:
      for k,v in self._keys.items():
        
        if not key in k:
          continue
        
        if not k.startswith(key):
          continue
        
        splitted = k.split('.')
        if level >= len(splitted):
          flattened[splitted[-1]] = v 
        else:
          flattened['.'.join(splitted[level:])] = v    
    
    fl = ConfigHandler(self.config, level=level, freeze=self.freeze)  
    fl._keys = flattened
    
    return fl
    
  def get(self, key, default=None):
    """
    Get value for dictionary key or return default
    
    :param key:     dictionary key to get value for
    :type key:      str
    :param default: default value to return if key does not exists
    """
    
    if key in self._keys:
      value = self.config.get(self._keys[key], default)
      return self._format(value)
      
    return default
  
  def get_attributes_at_level(self, level=0):
    """
    Return attribute names at a given level in a nested dictionary
    
    :param level: level from which to return attributes
    :type level:  int
    """
    
    attributes = []
    for key in self.keys():
      key = key.split('.')
      if len(key) > level or level < 0:
        attributes.append(key[level])
    
    return sorted(set(attributes))
  
  def get_level_for_attribute(self, attribute, keys=None):
    """
    Get the level associated to an attribute name.
    
    Search for the attribute in all dictionary keys or a
    subset through the `keys` attribute.
    Return a list of tuples listing (level, number of keys)
    
    :param attribute: attribute to return level for
    :type attribute:  str
    :param keys:      dictionary keys to search attribute 
                      name in. Optional.
    :type keys:       list of strings.
    """
    
    if keys:
      if not isinstance(keys, (tuple,list)):
        keys = [keys]
    else:
      keys = self._keys.values()  
    
    levels = []
    for key in keys:
      if attribute in key:
        levels.append(key.split('.').index(attribute))
    
    return [(l,levels.count(l)) for l in set(levels)]
    
  @property
  def isnested(self):
    """
    Test if dictionary is nested
    
    :return: nested or not
    :rtype:  bool
    """
    
    return any('.' in key for key in self.keys())
  
  def items(self):
    """
    :return: list of key,value pairs
    :rtype:  list of tuples
    """
    
    return [(k, self._format(self.config[v])) for k,v in self._keys.items()]
  
  def keys(self):
    """
    Return a set of the dictionary keys
    
    :return: dictionary keys
    :rtype:  set
    """
    
    return set(self._keys.keys())
  
  def load(self, config):
    """
    Load configuration dictionary.
    
    This will clear any configuration dictionary already
    loaded and reinitialize the current ConfigHandler class
    as root for the new configuration.
    
    :param config: configuration
    :type config:  dict
    """
    
    assert isinstance(config, dict), 'config attribute needs to be of type dict'
    
    # Clear current config
    self.config.clear()
    self._keys.clear()
    
    self.config.update(_flatten_nested_dict(config))
    self._resolve_config_level(self._reskeys)
    
  def remove(self, key):
    """
    Remove a key,value pair from the dictionary
    
    The target key is removed from self._keys by default
    effectively removing it from the (sub)dictionary
    representation leaving the source configuration dictionary
    untouched.
    
    If the ConfigHandler instance is not frozen, the key/value
    pair will also be removed from the source configuration
    
    :param key:   dictionary key to remove
    :type key:    str
    """
    
    assert key in self._keys, KeyError('Key "{0}" not in dictionary'.format(key))
    
    if not self.freeze:
      del self.config[self._keys[key]]
    
    del self._keys[key]  
  
  def search(self, pattern, regex=False, level=0):
    """
    Search the dictionary based on key names (strings) with support for
    Unix style wildcard expansion (using fnmatch) or regular expressions.
    
    Wildcard and regular expression search is particular usefull for search
    of nested dictionaries where the keys use dot seperation of key names 
    to represent the hierachy as in:
    
      `key_x.key_y.key_z`
    
    :param pattern: pattern to search for
    :type pattern:  str
    :param regex:   pattern is a regular expression
    :type regex:    bool
    :return:        search result.
    :rtype:         ConfigHandler object
    """
    
    match = []
    if not isinstance(pattern, (tuple,list)):
      pattern = [pattern]
    
    for p in pattern:  
      if not regex:
        match.extend([self._keys[key] for key in self._keys if fnmatch(key, p)])
      else:
        regex = re.compile(p)
        match.extend([self._keys[key] for key in self._keys if regex.match(key)])
    
    # If no match, return empty ConfigHandler
    if not len(match):
      return ConfigHandler(freeze=self.freeze, format_value=self.format_value)
         
    return self.subdict(match, level=level)
      
  def set(self, key, value):
    """
    Update and/or add key,value pair to dictionary
    
    Do not allow addition of new key,value pairs if the 
    dictionary is frozen
    
    :param key:   dictionary key to update/add
    :type key:    str
    :param value: dictionary value to update/add
    """
    
    if key not in self._keys and self.freeze:
      raise KeyError('Unable to add new key "{0}" to frozen dictionary'.format(key))
      
    self.config[self._keys.get(key,key)] = value
      
  def subdict(self, keys, level=0):
    """
    Return a new ConfigHandler instance reflecting a subdictionary
    
    :param keys: subdictionary keys
    :type keys:  list
    """
    
    return ConfigHandler(self.config, 
                         keys, 
                         freeze=self.freeze,
                         format_value=self.format_value,
                         level=level)  

  def update(self, other):
    
    if isinstance(other, ConfigHandler):
      add_count = 0
      for k,v in other._keys.items():
        if not k in self._keys:
          self._keys[k] = v
          add_count += 1
        if not v in self.config:
          self.config[v] = other.config[v]
    elif isinstance(other, dict):
      other = _flatten_nested_dict(other)
      self.config.update(other)
    else:
      logging.error('Attribute not an instance of ConfigHandler or dict')  
    
    self._resolve_config_level()
    
  def values(self):
    """
    :return: dictionary values
    :rtype:  list
    """
    
    return [self._format(self.config[key]) for key in self._keys.values()]
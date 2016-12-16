# -*- coding: utf-8 -*-

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
    """
    
    def __init__(self, config={}, keys=None, freeze=False, format_value=ConfigFormatter, level=0):
        """
        Implement class __init__ method
        
        :param config:       dictionary to manage
        :type config:        dict
        :param freeze:       allow addition of new keys or removal of keys
        :type freeze:        bool
        :param format_value: parse the value through the custom ConfigFormatter string
                             formatting class before returning
        :type format_value:  bool
        """
        
        self._config = None
        self._weakref_config(config)
        
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
        
        All __dict__ attributes except the _config dictionary are deepcopied.
        For the _config dictionary a copy is made for only those keys that 
        reflect the (sub)dictionary of the class instance.
        """
        
        new = ConfigHandler.__new__(ConfigHandler)
        memo[id(self)] = new
        
        for n, v in self.__dict__.items():
            if not n == '_config':
                setattr(new, n, copy.deepcopy(v, memo))
        
        new._weakref_config(dict([(v,self._config[v]) for k,v in self._keys.items()]))
        
        return new
    
    def __contains__(self, key):
        """
        Implement class __contains__ method
        This is the equivalent of the dict __contains__ method in that it only
        checks the first level of a nested dictionary for the key.
        
        :return: if the dictionary contains the key at the first level
        :rtype:  bool
        """
        
        return self.has_key(key)
    
    def __eq__(self, other):
        """
        Test equality (==) in dictionary keys between two ConfigHandler
        instances
        
        :param other: other ConfigHandler instance to test for
        :type other:  ConfigHandler instance
        """
        
        if isinstance(other, ConfigHandler):
            return self.keys() == other.keys()
    
    def __ne__(self, other):
        """
        Test inequality (!=) in dictionary keys between two ConfigHandler
        instances
        
        :param other: other ConfigHandler instance to test for
        :type other:  ConfigHandler instance
        """
        
        if isinstance(other, ConfigHandler):
            return self.keys() != other.keys()
    
    def __lt__(self, other):
        """
        Test if current ConfigHandler contains less (<) keys than other
        ConfigHandler.
        
        :param other: other ConfigHandler instance to test for
        :type other:  ConfigHandler instance
        """
        
        if isinstance(other, ConfigHandler):
            return len(self) < len(other)
    
    def __gt__(self, other):
        """
        Test if current ConfigHandler contains more (>) keys than other
        ConfigHandler.
        
        :param other: other ConfigHandler instance to test for
        :type other:  ConfigHandler instance
        """
        
        if isinstance(other, ConfigHandler):
            return len(self) > len(other)
    
    def __le__(self, other):
        """
        Test if current ConfigHandler contains equal or less (<=) keys
        than other ConfigHandler.
        
        :param other: other ConfigHandler instance to test for
        :type other:  ConfigHandler instance
        """
        
        if isinstance(other, ConfigHandler):
            return len(self) <= len(other)
    
    def __ge__(self, other):
        """
        Test if current ConfigHandler contains equal or more (>=) keys
        than other ConfigHandler.
        
        :param other: other ConfigHandler instance to test for
        :type other:  ConfigHandler instance
        """
        
        if isinstance(other, ConfigHandler):
            return len(self) >= len(other)
    
    def __add__(self, other):
        """
        Implements addition (+).
        
        Add (sub)dictionary keys from other to self using the add method.
        Addition equals dictionary updating but without replacement of 
        equal keys in self.
        
        :param other: other ConfigHandler instance
        :type other:  ConfigHandler instance
        
        :return:      New ConfigHandler instance with added keys
        :rtype:       ConfigHandler instance
        """
        
        addition = copy.deepcopy(self)
        addition.add(other)
        
        return addition
    
    def __iadd__(self, other):
        """
        Implements inplace addition (+=).
        
        Add (sub)dictionary keys from other to self using the add method.
        Addition equals dictionary updating but without replacement of 
        equal keys in self.
        
        :param other: other ConfigHandler instance
        :type other:  ConfigHandler instance
        """
        
        self.add(other)
        return self
        
    def __sub__(self, other):
        """
        Implements subtraction (-).
        
        Subtract (sub)dictionary keys of other from
        self. Does not remove key,value pairs in
        self._config.
        
        :param other: other ConfigHandler instance
        :type other:  ConfigHandler instance
        """
        
        subtract = copy.deepcopy(self)
        subtract.sub(other)
        
        return subtract
    
    def __isub__(self, other):
        """
        Implements implace subtraction (-=).
        
        Subtract (sub)dictionary keys of other from
        self. Does not remove key,value pairs in
        self._config.
        
        :param other: other ConfigHandler instance
        :type other:  ConfigHandler instance
        """
        
        subtract = copy.deepcopy(self)
        subtract.sub(other)
        
        return subtract
         
    __radd__ = __add__
    __rsub__ = __sub__
    
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
            query = self.get(key)
            if query:
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
        
        query = self.get(key)
        if query:
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
        
        propobj = getattr(self.__class__, key, None)
        
        if not '_initialised' in self.__dict__:
            return dict.__setattr__(self, key, value)
        elif isinstance(propobj, property) and propobj.fset:
            propobj.fset(self, value)
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
        
        propobj = getattr(self.__class__, key, None)
        
        if isinstance(propobj, property) and propobj.fset:
            propobj.fset(self, value)
        elif key in self._keys:
            self.set(key, value)
        else:
            dict.__setattr__(self, key, value)
    
    def __str__(self):
        """
        Implement class __str__ method.
        
        Return a print friendly overview of the current settings.
        Parameter placeholders are not resolved.
        
        :return: print friendly overview of settings.
        :rtype:  str
        """
        
        overview = []
        for k in sorted(self.keys()):
            if self._keys[k] in self._config:
                value = self._config[self._keys[k]]
            
                # Encode strings to UTF-8
                if type(value) in (str, unicode):
                    value = value.encode('utf-8')
            
                overview.append('{0}: {1}\n'.format(k, value))
        
        return ''.join(overview)
    
    def _weakref_config(self, config):
        """
        Setup a weak reference to the root instance of the 
        config dict if not done so already.
        
        :param config:       dictionary to make a weak reference to
        :type config:        dict
        """
        
        if not isinstance(config, DictWrapper):
            wrapped_config = DictWrapper(config)
            self._config = weakref.ref(wrapped_config)()
        else:
            self._config = config
    
    def _resolve_config_level(self, keys=None):
        """
        Set the keys in self._keys to reflect the attribute level
        in a nested dictionary and resolve attribute order when
        overloading similar attributes.
        """
        
        for key in keys or self._config.keys():
            splitted = key.split('.')
            if self.level >= len(splitted):
                self._keys[splitted[-1]] = key
            else:
                self._keys['.'.join(splitted[self.level:])] = key
    
    def _leveled_dict_copy(self):
        """
        Return a copy of the (sub)dictionary the ConfigHandler object
        represents
        
        :rtype: dict
        """
        
        return dict([ (key,self._config[value]) for key,value in self._keys.items() ])
    
    def _format(self, value):
        """
        Format values that have Python .format minilaguage placeholders.
        
        :param value: value to format
        :type value:  string
        
        :rtype:       string
        """
        
        try:
            return self.format_value.format(value)
        except:
            return value
        
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
    
    def contains(self, key):
        """
        Check if key is in dictionary at any level
        
        :return: if the dictionary contains the key
        :rtype:  bool
        """
        
        for k in self._keys:
            if key in k:
                return True
        
        return False 
    
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
        
        fl = ConfigHandler(self._config, level=level, freeze=self.freeze)
        fl._keys = flattened
        
        return fl
    
    def get(self, key, default=None):
        """
        Get value for dictionary key or return default
        
        The get method searches the dictionary keys in two ways:
        
        * Return the value if the full key is present in the dictionary
          keys list. The key may be a dot seperated string representing
          a nested dictinary key.
        * In case of a nested dictionary, match the key in the first
          level of the dictionary.
        
        :param key:     dictionary key to get value for
        :type key:      str
        :param default: default value to return if key does not exists
        """
        
        if key in self._keys:
            value = self._config.get(self._keys[key], default)
            return self._format(value)
        
        query = self.search('^{0}(?=.|$)'.format(key), regex=True, level=self.level+1)
        if len(query) == 1 and key in query._keys.values():
            return query.get(list(query._keys)[0])
        if len(query) == 1 and key in query._keys.keys():
            return query.get(key)
        if len(query):
            return query
        
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
    
    def levels(self):
        """
        Return number of levels in a nested dictionary
        
        :return: number of dictionary levels
        :rtype:  int
        """
        
        return max([len(n.split('.')) for n in self.keys()])
    
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
        self._config.clear()
        self._keys.clear()
        
        self._config.update(_flatten_nested_dict(config))
        self._resolve_config_level(self._reskeys)
    
    def remove(self, key):
        """
        Remove a key,value pair from the dictionary
        
        The target key is removed from self._keys by default effectively
        removing it from the active (sub)dictionary representation leaving
        the source configuration dictionary untouched.
        
        If the ConfigHandler instance is not frozen, the key/value pair will
        also be removed from the source configuration.
        
        ..  note:: When using chained attribute access (dot notation)
                   to remove a nested parameter in a frozen dictionary, the
                   last (sub)dictionary in the chain is the active one
                   resulting in the key,value pair still being available in 
                   the other ones.
        
        :param key:   dictionary key to remove
        :type key:    str
        """
        
        assert key in self._keys, KeyError('Key "{0}" not in dictionary'.format(key))
        
        if not self.freeze:
            del self._config[self._keys[key]]
        
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
        
        self._config[self._keys.get(key,key)] = value
    
    def subdict(self, keys, level=0):
        """
        Return a new ConfigHandler instance reflecting a subdictionary
        
        :param keys: subdictionary keys
        :type keys:  list
        """
        
        return ConfigHandler(self._config,
                             keys,
                             freeze=self.freeze,
                             format_value=self.format_value,
                             level=level)
    
    # Python dictionary methods
    def clear(self):
        """
        Clear the dictionary of all key,value pairs
        
        Do not allow clearance of key,value pairs if the
        dictionary is freezed
        """
        
        if self.freeze:
            raise KeyError('Unable to clear freezed dictionary'.format(key))
        
        self._keys = []
        self._config.clear()
    
    def has_key(self, key):
        """
        Checks the first level of a nested dictionary for the key.
        
        Both self._keys and self._config are checked for the key to ensure that
        local changes to self._keys do not run "out of sync" with self._config
        
        This method is deprecated in Python 3 in favor of `key in d`.
        In the ConfigHandler class this method is used by the __contains__
        magic method.
        
        :return: if the dictionary contains the key at the first level
        :rtype:  bool
        """
        
        for k in self._keys:
            if k.startswith(key) and self._keys[k] in self._config:
                return True
        
        return False
            
    def items(self):
        """
        :return: list of key,value pairs
        :rtype:  list of tuples
        """
        
        return [(k, self._format(self._config[v])) for k,v in self._keys.items()]
    
    def keys(self):
        """
        Return dictionary keys in the active (sub)dictionary
        
        :return: dictionary keys
        :rtype:  set
        """
        
        return [key for key,value in self._keys.items() if value in self._config]
    
    def add(self, other):
        """
        Add unique keys from other to self
        
        :param other: other ConfigHandler instance
        :type other:  ConfigHandler instance
        """
        
        self.update(other, replace=False)
    
    def sub(self, other):
        """
        Remove keys in other from self
        
        :param other: other ConfigHandler instance
        :type other:  ConfigHandler instance
        """
        
        if isinstance(other, ConfigHandler):
            toremove1 = [k for k in other._keys.values() if k in self._keys.values()]
            toremove2 = [k for k,v in self._keys.items() if v in toremove1]
            for key in toremove2:
                del self._keys[key]
    
    def update(self, other, replace=True):
        """
        Update self with unique keys from other not in self
        
        :param other:   other ConfigHandler instance
        :type other:    ConfigHandler instance
        :param replace: in case of equal keys between self and other, replace
                        value of self with other.
        :type replace:  bool
        """
        
        if isinstance(other, ConfigHandler):
            for k,v in other._keys.items():
                
                if k in self._keys and not replace:
                    pass
                else:
                    self._keys[k] = copy.deepcopy(v)
                
                # Update self_config if needed
                if not v in self._config:
                    self._config[v] = other._config[v]
                    
        elif isinstance(other, dict):
            other = _flatten_nested_dict(other)
            self._config.update(other)
        else:
            raise TypeError('Attribute not an instance of ConfigHandler or dict')
        
    def values(self):
        """
        Implementation of dict `values` method.
        
        Returns values for all keys at every level of a nested dictionary
        
        :return: dictionary values
        :rtype:  list
        """
        
        return [self._format(self._config[key]) for key in self._keys.values()]
# -*- coding: utf-8 -*-

import copy
import json
import os
import sys

from   twisted.logger import Logger 
logging = Logger()

def _open_anything(source):
  
  # Check if the source is a file and open
  if os.path.isfile(source):
    logging.debug("Reading file from disk {0}".format(source))
    return open(source, 'r')
    
  # Check if source is file already openend using 'open' or 'file' return
  elif hasattr(source, 'read'):
    logging.debug("Reading file %s from file object" % source.name)
    return source
    
  # Check if source is standard input
  elif source == '-':
    logging.debug("Reading file from standard input")
    return sys.stdin
    
  else:
    # Check if source is a URL and try to open
    try:
      
      import urllib2, urlparse
      if urlparse.urlparse(source)[0] == 'http':
        result = urllib.urlopen(source)
        loggin.debug("Reading file from URL with access info:\n %s" % result.info())
        return result
    except:
      logging.info("Unable to access URL")    
    
    # Check if source is file and try to open else regard as string
    try:
      return open(source)
    except:
      logging.debug("Unable to access as file, try to parse as string")
      from   StringIO import StringIO
      return StringIO(str(source))


class _ConfigHandlerCommon(object):
  
  def __call__(self):
    
    """
    Implement class __call__ method
    
    :return: full configuration dictionary
    """
    
    return self._config
  
  def __contains__(self, key):
    
    """
    Implement class __contains__ method
    
    :return: Boolean, if key in self._config
    """
    
    return key in self._config
    
  def __getitem__(self, key):
    
    """
    __getitem__ overload.
    
    Get self._config values using dictionary style access, fallback to
    default __getitem__

    :param str name: attribute name
    :return: attribute
    """
    
    if key in self._config:
      return self.get(key)
    return self.__dict__[key]
  
  def __getattr__(self, key):
    
    """
    __getattr__ overload.
    
    Expose self._config dictionary keys as class attributes.
    fallback to the default __getattr__ behaviour.

    :param str name: attribute name
    :return: attribute
    """
    
    if key in self._config:
      return self.get(key)
    return object.__getattr__(self, key)
  
  def __setattr__(self, key, value):
    
    """
    __setattr__ overload.
    
    Set self._config dictionary entries using class attribute setter methods
    fallback to the default __setattr__ behaviour.

    :param str name: attribute name.
    :param mixed value: attribute value
    """
    
    if not '_initialised' in self.__dict__:
      return dict.__setattr__(self, key, value)
    elif key in self._config:
      self.set(key, value)
    else:
      self.__setitem__(key, value)
  
  def __setitem__(self, key, value):
    
    """
    __setitem__ overload.
    
    Set self._config values using dictionary style access, fallback to
    default __setattr__

    :param str name: attribute name
    :param mixed value: attribute value
    """  
  
    if key in self._config:
      self.set(key, value)
    else:
      dict.__setattr__(self, key, value)
        
  def __repr__(self):
 
   """
   Implement class __repr__ method
 
   :return: class instance information
   :rtype:  string
   """
   
   instance = 'all'
   if hasattr(self,'_instance'):
     instance = ', '.join(self._instance)
   
   return "<{0} object {1} for instances: {1}>".format(type(self).__name__, id(self), instance)
  
  def __str__(self):
    
    """
    Implement class __str__ method.
    
    :return: print friendly overview of settings
    """
    
    overview = []
    for k in sorted(self._config.keys()):
      overview.append('{0}: {1}\n'.format(k,self._config[k]))
    
    return ''.join(overview)
  
  def set(self, key, value, strict=False):
    
    if key not in self._config and strict:
      raise KeyError('No key named "{0}" in configuration {1}'.format(key, ', '.join(self._instance)))
  
    self._config[key] = value
  
  def get(self, key, default=None):
    
    return self._config.get(key, default)
  
  def items(self):
    
    return self._config.items()
  
  def remove(self, key):
    
    if key in self._config:
      del self._config[key]
  
  def update(self, configdict, strict=True):
    
    """
    Update the configuration dictionary with key,value pairs from another 
    dictionary. If 'strict' than raise an error if the key is not in the 
    dictionary.
    
    :param configdict: Dictionary with configuration settings.
    :type configdict: Dictionary
    """
    
    assert type(configdict) == dict, TypeError("Custom configuration needs to be defined as a dictionary")
    if strict:
      for key,value in configdict.items():
        if key not in self._config and strict:
          self._config[key] = value
    else:
      self._config.update(configdict)


class ConfigHandler(_ConfigHandlerCommon):
  
  """
  ConfigHandler class
  """
  
  def __init__(self, config, instance=None):
    
    self._config      = config
    self._instance    = instance
    
    self._defaults    = copy.copy(config)
    self._initialised = True
          
  def default(self, key):
    
    return self._defaults.get(key, None)
    
  def revert(self, key):
    
    self.set(key, self.default(key))
            
    
class MetaConfigHandler(_ConfigHandlerCommon):
  
  """
  MetaConfigHandler class
  
  Manages settings for all module functions and classes available module wide.
  The GRAMMATICS_MASTER_CONFIG dictionary in grammatics.data.settings serves as 
  the default source of settings. 
  Settings are defined in principle by the function or class name followed by 
  the setting variable name, dot seperated. In practice, any string will work 
  
  Settings for multiple classes or function can be combined in one dictionary 
  but with the risk of similar named functions to be overwritten. The settings
  are resolved in class name order allowing control over the overload process
  e.g. Global settings overloaded by Local ones. 
  
  The default configuration may be updated by the user from a dictionary with
  custom configuration settings.
  Functions or classes requesting configuration settings will get a copy of the
  settings from the main configuration to allow for safe overloading the settings
  for that particular instance only.
  
  :param config:    Default configuration dictionary to initiate class with
  :type config:    Dictionary
  :param defaults:  Default classes for which the settings should always be 
                    included in the returned ConfigHandler object
  :type defaults:  List
  """
  
  def __init__(self, config, defaults=[]):
    
    assert type(config) == dict, TypeError("Default configuration needs to be defined as a dictionary, got: {0}".format(config))
    self._config = config
    
    assert type(defaults) == list, TypeError("Default classes need to be defined as a list, got: {0}".format(defaults))
    self._defaults = defaults
    
    self._instance = [key.split('.', 1)[-1] for key in self._config.keys()]
    self._initialised = True
    
  def fetch(self, instance=[]):
    
    """
    Return a copy of the configuration settings for particular function(s) or
    class instance(s) as a ConfigHandler object.
    
    :param instance: Function or class name(s) to return configuration for.
    :type instance: String or list of strings
    """
    
    # Cast input to list
    if type(instance) == str:
      instance = [instance]
    
    # Merge default settings and remove duplicates
    instance = set([n for n in instance] + self._defaults)
    
    # Make (nested) dictionary
    selection = {}
    for a in instance:
      selection.update(dict([ (key.split('.', 1)[-1], value) for key,value in self._config.items() if key.startswith(a) ]))

    # Return a selection configuration dictionary wrapped in a controller object
    logging.debug('Fetch configuration for instances: {0}'.format(' '.join(instance)))
    return ConfigHandler(selection, instance=instance)
  
  def load(self, jsonfile):
    
    """
    Update the default pylie configuration with a custom configuration
    dictionary loaded from a JSON file format.
    
    :param jsonfile: configuration file in JSON format
    :type jsonfile: File path or file like object
    """
    
    fileobject = _open_anything(jsonfile)
    data = json.load(fileobject)
    
    self.update(data, strict=False)
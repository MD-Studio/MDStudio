# -*- coding: utf-8 -*-

import json
import os
import sys
import weakref

from   twisted.logger import Logger

from   .config_handler import ConfigHandler
from   .config_format  import ConfigFormatter

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

class DictWrapper(dict):
  
  config = None
  
  def __call__(self):
    
    return self.config

class ConfigManager(object):
  
  """
  ConfigManager class
  
  Manages the settings for all packages, modules or functions defined as 
  dictionary of combined global settings provided at class initialisation 
  or individually using the `load` methods.
  
  Internally, the settings are stored as a dictionary with keys representing
  the setting hierarchy as dot seperated string. For example:
  
  * <package name>.<class name>.<function name>.<attribute>
  * <package name>.<function name>.<attribute>
  
  The package name and attribute name (or setting name) are required, 
  class and function names are optional.
  
  A subset of settings can be retrieved using the `fetch` method. 
  The `fetch` method returns a copy of the requested settings from the main
  settings dictionary in package name order. This allows for a safe
  overloading of the settings for that particular instance only.
  The returned subset supports Python string formatting for string based
  settings in which the replacement token is the same dot seperated setting
  name. For example:
  
    'database_path': '{system.app_dir}/database'
  
  allows the datbase path the be resolved dynamically using the active 
  application path derived from the system package.
    
  :param config:    default configuration dictionary to initiate class with
  :type config:     dict
  :param defaults:  default classes for which the settings should always be 
                    included in the returned ConfigHandler object
  :type defaults:   list
  """
  
  def __init__(self, config={}, defaults=[]):
    
    assert type(config) == dict, TypeError("Default configuration needs to be defined as a dictionary, got: {0}".format(config))
    self._config = DictWrapper()
    
    assert type(defaults) == list, TypeError("Default classes need to be defined as a list, got: {0}".format(defaults))
    self._defaults = defaults
    
    self._format = ConfigFormatter
    
  def fetch(self, instance=[]):
    
    """
    Return a copy of the configuration settings for particular function(s) or
    class instance(s) as a ConfigHandler object.
    
    :param instance: function or class name(s) to return configuration for.
    :type instance: string or list of strings
    """
    
    # Cast input to list
    if type(instance) == str:
      instance = [instance]
    
    # Add instance to default settings
    instance = self._defaults + instance
    
    # Return a selection configuration dictionary wrapped in a controller object
    logging.debug('Fetch configuration for instances: {0}'.format(' '.join(instance)))
    return ConfigHandler(weakref.ref(self._config)(), format_value=self._format)
  
  def load_dict(self, settings_dict, component_name):
    
    formatted_settings = {}
    for setting_name, setting_value in settings_dict.items():
      if component_name and not setting_name.startswith(component_name):
        formatted_settings['{0}.{1}'.format(component_name, setting_name)] = setting_value
      else:
        formatted_settings[setting_name] = setting_value
    
    self.update(formatted_settings, strict=False)
    
  def load_json(self, jsonfile):
    
    """
    Update the default configuration with a custom configuration
    dictionary loaded from a JSON file format.
    
    :param jsonfile: configuration file in JSON format
    :type jsonfile: File path or file like object
    """
    
    fileobject = _open_anything(jsonfile)
    data = json.load(fileobject)
    
    self._config.update(data)
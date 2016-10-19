#!/usr/bin/env python

import collections
import json

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

def _flatten_nested_dict(config, parent_key='', sep='.'):
  """
  Flatten a nested dictionary by concatenating all 
  nested keys. 
  Keys are converted to a string representation if
  needed.
  
  :param config:     dictionary to flatten
  :type config:      dict
  :param parent_key: leading string in concatenated keys
  :type parent_key:  str
  :param sep:        concatenation seperator
  :type sep:         str
  :return:           flattened dictionary
  :rtype:            dict
  """
  
  items = []
  for key,value in config.items():
    
    # parse key to string if needed
    if type(key) not in (str,unicode):
      logging.debug('Dictionary key {0} of type {1}. Parse to string'.format(key, type(key)))
      key = str(key)
    
    new_key = parent_key + sep + key if parent_key else key
    if isinstance(value, collections.MutableMapping):
      items.extend(_flatten_nested_dict(value, new_key, sep=sep).items())
    else:
      items.append((new_key, value))
  
  return dict(items)

def _nest_flattened_dict(config, sep='.'):
  """
  Convert a dictionary that has been flattened by the
  `_flatten_nested_dict` method to a nested representation
  
  :param config:     dictionary to nest
  :type config:      dict
  :param sep:        concatenation seperator
  :type sep:         str
  :return:           nested dictionary
  :rtype:            dict
  """
  
  nested_dict = {}
  for key,value in config.items():
  
    splitted = key.split(sep)
    if len(splitted) == 1:
      nested_dict[key] = value
  
    d = nested_dict
    for k in splitted[:-1]:
      if not k in d:
        d[k] = {}
      d = d[k]
  
    d[splitted[-1]] = value
  
  return nested_dict

def config_to_json(config, tofile=None):
    """
    Export the setting in a ConfigHandler instance to JSON format.
    Optionally write the JSON construct to file
    
    :param config: configuration to export
    :type config:  ConfigHandler
    :param tofile: filepath to write exported JSON to
    :type tofile:  str
    """
    
    nested_dict = _nest_flattened_dict(config())
    jsonconfig = json.dumps(nested_dict, indent=4, sort_keys=True)
    
    if tofile:
        with open(tofile, 'w') as cf:
            cf.write(jsonconfig)
    else:
        return jsonconfig    

def exit_config(settings):
    """
    Config component bootstrap routines
    
    Save the updated global configuration back to the settings.json file
    
    :param settings: global and module specific settings
    :type settings:  dict or dict like object
    """
    
    from lie_config import get_config
  
    config = get_config()
    app_config = config.get('system.app_config')
    if app_config:
        config_to_json(config, app_config)
    

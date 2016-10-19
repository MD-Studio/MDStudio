# -*- coding: utf-8 -*-

"""
LIEStudio configuration management component

The LIE config package streamlines the access to both application wide
as well as module or user specific settings within the Python runtime,
between processes or machines over a network.

The design of the lie_config module mimics that of Pythons well known
logging module in that an instance of a configuration class 
(ConfigHandler class) initiated somewhere early on in the program life
cycle is accessible by any module in the active Python runtime.
This philosophy is extended to inter-process and inter-machine 
configuration by providing WAMP endpoints.

An example of initiating a global ConfigHandler class from a configuration
stored as JSON file
::
    import json
    import lie_config

    config = lie_config.get_config()
    config.load(json.load('config.json'))

A ConfigHandler class is a Python dictionary class on steroids. 
It functions as a wrapper around a nested configuration dictionary and
extends it with functions to:

* Query the dictionary anywhere in the nested hierarchy
* Access nested layers or values using attribute acces, item access or
  get and set actions.
* Perform key/value overloading enabling for instance user settings that
  have precedence over module settings that again have predenence over
  global system settings.
* Value placeholders. Use any dictionary key as placeholder in another
  value. The resulting 'dynamic' value will be resolved at the time of
  access.
"""

import os

__module__    = 'lie_config'
__docformat__ = 'restructuredtext'
__version__   = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__    = 'Marc van Dijk'
__status__    = 'pre-release beta1'
__date__      = '15 april 2016'
__licence__   = 'Apache Software License 2.0'
__url__       = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) VU University, Amsterdam"
__rootpath__  = os.path.dirname(__file__)
__all__       = ['get_config','ConfigHandler','configwrapper','config_to_json']

# For Python => 3.3, import inspect.signature
# else import funcsigs backport.
try:
  from inspect import signature
except:
  from funcsigs import signature

# Component imports
from .config_handler import ConfigHandler
from .config_io      import exit_config, config_to_json

# Define module public API
settings = None
oninit   = None
onexit   = exit_config

# Runtime wide configuration store
configurations = {}

def get_config(name='default'):
  
  if not name in configurations:
    configurations[name] = ConfigHandler()
  
  return configurations.get(name, None)

class configwrapper(object):
  
  """
  configwrapper class
  
  Decorator class responsible for replacing class or function keyword arguments 
  by their equivalents from the module wide configuration.
  
  Without any arguments to the decorator, the decorated function name is used
  to retrieve the configuration managed by a ConfigHandler instance.
  The 'default' ConfigHandler is used by default unless specified otherwise
  by the `confighandler` keyword argument.
  All function keyword arguments are replaced by their equivalents from the 
  configuration except if they are defined in the call to the function (local
  overload).
  
  With a string as argument to the decorator the configuration for that
  particular name will be searched for at any level in the configuration using
  the ConfigHandler `search` method. Both unique function names or a '.' (dot)
  seperated nested function name are accepted. The latter is more specific in
  case the same function name is used in different scopes.
  
  Finally a list of strings as argument to the decorator allows the configuration
  to be resolved by overloading the configuration in the lists order.
  This feature is usefull if an argument to a function is not defined specific
  for that function in the configuration but is define in another (global) scope.
  
  If the function defines **kwargs in its argument string, all other parameters
  in the ConfigHandler instance resolved for that function are passed to the
  function. These parameters may be explicitly defined for that function by
  name (e.a '<function name>.<keyword argument name>') or resolved by resolution
  order to the keyword argument name.
  
  :param instance:      function or class name for which to retrieve configuration
                        multiple names allowed for a specific resolution order.
  :type instance:       str or list
  :param confighandler: specific ConfigHandler instance to get configuration from
  :type confighandler:  str
  """
  
  def __init__(self, instance=None, confighandler='default'):
    
    self.instance = instance
    if self.instance and not isinstance(self.instance, (tuple,list)):
      self.instance = [self.instance]
    
    self.confighandler = confighandler
      
  def __call__(self, func):
    
    # If the instance names to fetch are not defined, use function or class name
    if not self.instance:
      self.instance = [func.__name__]
    query = ['*{0}*'.format(i) for i in self.instance]
    
    # Get parameter names from the global config.
    settings = get_config(name=self.confighandler).search(query)
    
    # Determine level at wich to flatten config file
    levels = []
    for q in self.instance:
      levels.extend([l[0] for l in settings.get_level_for_attribute(q)])
    level = 0
    if len(levels):
      level = min(levels)
    settings = settings.flatten(resolve_order=self.instance, level=level+1)
    
    def wrapped_f(*args, **kwargs):
      
      fsig = signature(func)
      
      # Inspect the function for keyword arguments.
      # Replace by settings value if not defined in kwargs
      for param in fsig.parameters.values():
        if not param.default == param.empty and not param.name in kwargs and param.name in settings:
          kwargs[param.name] = settings[param.name]
       
      # If kwargs is defined in the functions arguments,
      # add all other keyword arguments not yet defined
      if 'kwargs' in fsig.parameters:
        for k,v in settings.dict(nested=True).items():
          if not k in kwargs:
            kwargs[k] = v
      
      return func(*args, **kwargs)
    return wrapped_f
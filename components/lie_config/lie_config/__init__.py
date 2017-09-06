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

.. code-block:: python

    import json
    import lie_config

    config = lie_config.get_config()
    config.load(json.load(open('config.json')))

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

__module__ = 'lie_config'
__docformat__ = 'restructuredtext'
__version__ = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__ = 'Marc van Dijk'
__status__ = 'pre-release beta1'
__date__ = '15 april 2016'
__licence__ = 'Apache Software License 2.0'
__url__ = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) VU University, Amsterdam"
__rootpath__ = os.path.dirname(__file__)
__all__ = ['get_config', 'ConfigHandler', 'configwrapper', 'config_to_json']

# For Python => 3.3, import inspect.signature
# else import funcsigs backport.
try:
    from inspect import signature
except BaseException:
    from funcsigs import signature

# Component imports
from mdstudio.config import ConfigHandler, config_to_json, configurations, get_config, configwrapper

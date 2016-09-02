# -*- coding: utf-8 -*-

"""
package:  lie_config

LIEStudio configuration management component
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

# Component imports
from .config_handler import MetaConfigHandler
from .wamp_services  import ConfigBackend

# Define module public API
settings = None
wampapi  = ConfigBackend
oninit   = None
onexit   = None
__all__  = ['MetaConfigHandler']
# -*- coding: utf-8 -*-

"""
package:  lie_componentbase

LIEStudio system component
"""

import inspect
import sys
import os

__module__    = 'lie_componentbase'
__docformat__ = 'restructuredtext'
__version__ = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__ = 'Marc van Dijk'
__status__ = 'pre-release beta1'
__date__ = '15 april 2016'
__licence__ = 'Apache Software License 2.0'
__url__ = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) 2016, Marc van Dijk, VU University, Amsterdam"
__rootpath__ = os.path.dirname(__file__)
__all__ = ['ComponentManager', 'BaseApplicationSession']

# Component imports
from .component_manager import ComponentManager
from .application_session import BaseApplicationSession, block_on
from .util import register, WampSchema, Schema, InlineSchema, validate_json_schema, validate_input, validate_output
from .config import PY3

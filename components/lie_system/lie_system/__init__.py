# -*- coding: utf-8 -*-

"""
package:  lie_system

LIEStudio system component
"""

import os

__module__ = 'lie_system'
__docformat__ = 'restructuredtext'
__version__ = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__ = 'Marc van Dijk'
__status__ = 'pre-release beta1'
__date__ = '15 april 2016'
__licence__ = 'Apache Software License 2.0'
__url__ = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) 2016, Marc van Dijk, VU University, Amsterdam"
__rootpath__ = os.path.dirname(__file__)
__all__ = ['ComponentManager', 'LieApplicationSession', 'WAMPTaskMetaData']

# Component imports
from .component_manager import ComponentManager
from .wamp_tools import LieApplicationSession
from .wamp_taskmeta import WAMPTaskMetaData

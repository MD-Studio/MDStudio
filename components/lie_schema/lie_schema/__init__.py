# -*- coding: utf-8 -*-

"""
package:  lie_schema

LIEStudio schema component
"""

import os

__module__ = 'lie_schema'
__docformat__ = 'restructuredtext'
__version__ = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__ = 'Marc van Dijk, Zefiros Software'
__status__ = 'pre-release beta1'
__date__ = '11 november 2017'
__licence__ = 'Apache Software License 2.0'
__url__ = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) VU University, Amsterdam"
__rootpath__ = os.path.dirname(__file__)

# Import settings
from .wamp_services import SchemaWampApi

# Define component public API
wampapi = SchemaWampApi

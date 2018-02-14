# -*- coding: utf-8 -*-

"""
package:  mdstudio

LIEStudio system component
"""

import sys

import os

__module__ = 'mdstudio'
__docformat__ = 'restructuredtext'
__version__ = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__ = 'Marc van Dijk'
__status__ = 'pre-release beta1'
__date__ = '15 april 2016'
__licence__ = 'Apache Software License 2.0'
__url__ = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) 2016, Marc van Dijk, VU University, Amsterdam"

is_python3 = (sys.version_info > (3, 0)) and (sys.version_info < (4, 0))

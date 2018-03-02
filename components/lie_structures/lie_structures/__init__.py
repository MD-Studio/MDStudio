# -*- coding: utf-8 -*-
"""
package:  lie_structures
LIEStudio small molecule cheminformatics functions
"""

import os

__module__ = 'lie_structures'
__docformat__ = 'restructuredtext'
__version__ = '{major:d}.{minor:d}'.format(major=0, minor=2)
__author__ = 'Marc van Dijk'
__status__ = 'pre-release beta1'
__date__ = '5 august 2016'
__licence__ = 'Apache Software License 2.0'
__url__ = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) VU University, Amsterdam"
__rootpath__ = os.path.dirname(__file__)

from .settings import STRUCTURES_SCHEMA as structures_schema
from .settings import settings
from .cheminfo_pkgmanager import CinfonyPackageManager

# Load the toolkits
paths = dict((k, v) for k, v in settings.items()
             if k in ('indy_path', 'rdk_path'))
toolkits = CinfonyPackageManager(paths)

__all__ = ['toolkits', 'structures_schema']

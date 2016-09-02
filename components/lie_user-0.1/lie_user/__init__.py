# -*- coding: utf-8 -*-

"""
package: lie_user

LIEStudio user management component
"""

import os

__module__    = 'lie_user'
__docformat__ = 'restructuredtext'
__version__   = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__    = 'Marc van Dijk'
__status__    = 'pre-release beta1'
__date__      = '15 april 2016'
__licence__   = 'Apache Software License 2.0'
__url__       = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) VU University, Amsterdam"
__rootpath__  = os.path.dirname(__file__)

from .settings import SETTINGS
from .wamp_services import UserWampApi
from .management import init_user, exit_user

# Define module public API
settings = SETTINGS
wampapi  = UserWampApi
oninit   = init_user
onexit   = exit_user
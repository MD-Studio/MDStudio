# -*- coding: utf-8 -*-

"""
file: test.py

Unit tests for the lie_config component
"""

import os
import sys
import unittest2
import json
import copy
import glob

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

# Get the Python version as some unittests differ between
# Python 2.x and 3.x
PY3 = sys.version_info.major == 3

from lie_config                     import *
from lie_config.config_orm_handler  import ConfigOrmHandler
from lie_config.config_io           import config_from_json

class _taskMeta(object):
    
    def custommethod(self):
        
        return "custom method"


class ConfigHandlerORMTests(unittest2.TestCase):
    """
    Unittest ConfigHandler ORM tests
    """
    
    _currpath = os.path.abspath(__file__)
    _settings_json = os.path.join(os.path.dirname(_currpath), '../', 'files', 'config_orm_test.json')
    
    def setUp(self):
        """
        ConfigHandlerTests class setup
        
        Load test settings file from config_orm_test.json
        """
        
        data = config_from_json(self._settings_json)
        
        # Setup ORM handler
        orm = ConfigOrmHandler(ConfigHandler)
        orm.add('_taskMeta', _taskMeta)
        
        self.settings = ConfigHandler(orm=orm)
        self.settings.load(data)
    
    def test_orm_mapper(self):
        
        b = self.settings._taskMeta
        self.assertTrue(hasattr(b, 'custommethod'))
        self.assertEqual(b.custommethod(), "custom method")

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
from lie_config.config_io           import (_flatten_nested_dict, config_from_yaml, config_from_ini, config_from_json,
                                            config_to_yaml, config_to_ini, config_to_json)
                                            
class ConfigHandlerIOTests(unittest2.TestCase):
    """
    Unittest ConfigHandler IO tests
    """
    
    _currpath = os.path.abspath(__file__)
    _settings_json = os.path.join(os.path.dirname(_currpath), 'files', 'config_handler_test')
    
    @classmethod
    def setUpClass(cls):
        """
        ConfigHandlerTests class setup
        
        Load the reference configuration
        """
        
        cls.data = json.load(open('{0}.json'.format(cls._settings_json)))
        cls.reference_config = ConfigHandler()
        cls.reference_config.load(cls.data)
    
    def tearDown(self):
        """
        Remove exported test files
        """
        
        for exp in glob.glob('{0}_exporttest.*'.format(self._settings_json)):
            os.remove(exp)
    
    def test_import_yaml(self):
        """
        Test import of configuration from YAML file
        """
        
        yamldata = config_from_yaml('{0}.yaml'.format(self._settings_json))
        config = ConfigHandler()
        config.load(yamldata)
        
        self.assertEqual(self.reference_config, config)

    def test_import_ini(self):
        """
        Test import of configuration from INI file
        """
        
        inidata = config_from_ini('{0}.ini'.format(self._settings_json))
        config = ConfigHandler()
        config.load(inidata)
        
        self.assertEqual(self.reference_config, config)
    
    def test_import_json(self):
        """
        Test import of configuration from JSON file
        """
        
        jsondata = config_from_json('{0}.json'.format(self._settings_json))
        config = ConfigHandler()
        config.load(jsondata)
        
        self.assertEqual(self.reference_config, config)
    
    def test_import_json(self):
        """
        Test import of configuration from JSON file
        """
        
        jsondata = config_from_json('{0}.json'.format(self._settings_json))
        config = ConfigHandler()
        config.load(jsondata)
        
        self.assertEqual(self.reference_config, config)
    
    def test_export_json(self):
        """
        Test export of configuration to JSON file
        """
        
        config_to_json(self.reference_config, tofile='{0}_exporttest.json'.format(self._settings_json))
        
    def test_export_yaml(self):
        """
        Test export of configuration to YAML file
        """
        
        config_to_yaml(self.reference_config, tofile='{0}_exporttest.yaml'.format(self._settings_json))
    
# -*- coding: utf-8 -*-

"""
file: test.py

Unit tests for the lie_config component

TODO: Add wamp_services unittests
"""

import os, sys
import unittest
import json

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

# Get the Python version as some unittests differ between 
# Python 2.x and 3.x
PY3 = sys.version_info.major == 3

# Test import of the lie_db database drivers
# If unable to import we cannot run the UserDatabaseTests
dbenabled = False
try:
  from lie_db import BootstrapMongoDB
  dbenabled = True
except:
  pass

from lie_config           import *
from lie_config.config_io import _flatten_nested_dict

formatted_example_config = {
  'system.port': 50000,
  'lie_logging.PrintingObserver.datefmt': '%m/%d/%Y %I:%M:%S',
  'lie_db.port': 27017,
  'lie_db.create_db': True,
  'lie_logging.LogObserver.datefmt': '%m/%d/%Y %I:%M:%S',
  'lie_db.dblog': '/usr/app/data/logs/mongodb.log',
  'lie_logging.PrintingObserver.format_event': '{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n',
  'user.dbpath': '/usr/app/data/user',
  'system.app_path': '/usr/app',
  'lie_logging.LogObserver.activate': False,
  'lie_db.dbname': 'liestudio',
  'lie_db.terminate_mongod_on_exit': False,
  'lie_logging.PrintingObserver.activate': True,
  'lie_db.dbpath': '/usr/app/data/liedb',
  'lie_db.host': 'localhost',
  'lie_logging.PrintingObserver.filter_predicate.log_level': 'debug',
  'lie_logging.PrintingObserver.filter_predicate.app_namespace': ' > 5',
  'lie_logging.LogObserver.filter_predicate.log_level': 'infp',
  'lie_logging.LogObserver.filter_predicate.app_namespace': ' > 3',
  'lie_logging.LogObserver.format_event': '{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n'
}

class ConfigDecoratorTests(unittest.TestCase):
    """
    Unittest the configuration decorator method
    """
    
    _currpath = os.path.abspath(__file__)
    _settings_json = os.path.join(os.path.dirname(_currpath), 'config_decorator_test.json')
        
    @classmethod
    def setUpClass(cls):
      """
      ConfigHandlerTests class setup
      
      Load test settings file from config_decorator_test.json
      """
      
      cls.data = json.load(open(cls._settings_json))
      settings = get_config()
      settings.load(cls.data)
    
    def test_single_function_decorator(self):
      """
      Test the decorator on a single function with a predefined
      ConfigHandler instance.
      Change the configuration elsewhere and see changes reflected in
      the next call to the function.
      """
      
      from .decorator_test import decorator_method_defined, change_value_elsewhere
      
      # configwrapper managed function, default behaviour
      self.assertEqual(decorator_method_defined(2), (4,6))
      
      # configwrapper managed function, local argument overload
      self.assertEqual(decorator_method_defined(2, lv=3), (6,6))
    
      # configwrapper managed function, changing the config
      # elshwere reflected in default behaviour
      change_value_elsewhere('decorator_method_defined.gv', 10)
      self.assertEqual(decorator_method_defined(2), (4,20))
      
    def test_undefined_function_decorator(self):
      """
      Test the decorator on a single function without arguments in
      global configuration.
      """
      
      from .decorator_test import decorator_method_undefined
        
      self.assertEqual(decorator_method_undefined(2), (2,4))
    
    def test_single_function_decorator_with_kwargs(self):
      """
      Test the decorator on a single function that also accepts
      additonal kyword arguments via **kwargs.
      This should result in the decorator passing all keyword
      arguments available for the function.
      """
      
      from .decorator_test import decorator_method_withkwargs
      
      self.assertEqual(decorator_method_withkwargs(2), (4, 6, {'nested': {'sec': True}, 'other': 'additional'}))
    
    def test_single_function_decorator_resolutionorder(self):
      """
      Test the decorator on a single function with a predefined
      ConfigHandler instance.
      The decorator is configured to resolve the function arguments
      in predefined overload order.
      """
      
      from .decorator_test import decorator_method_resolutionorder  
      
      self.assertEqual(decorator_method_resolutionorder(2), (20,6))
      
    def test_class_decorator(self):  
      """
      Test the decorator on a class with a predefined ConfigHandler
      instance.
      """
      
      from .decorator_test import decorator_class
      
      klass = decorator_class()
      self.assertEqual(klass.run(2), (4,6))
      self.assertEqual(klass.decorated_run(2), (20,30))
      
class ConfigHandlerTests(unittest.TestCase):
    """
    Unittest ConfigHandler class
    """
    
    _currpath = os.path.abspath(__file__)
    _settings_json = os.path.join(os.path.dirname(_currpath), 'config_handler_test.json')
        
    @classmethod
    def setUpClass(cls):
      """
      ConfigHandlerTests class setup
      
      Load test settings file from config_handler_test.json
      """
      
      cls.data = _flatten_nested_dict(json.load(open(cls._settings_json)))
      cls.settings = get_config()
      cls.settings.load(cls.data)
      
    def test_config_magicmethod(self):
      """
      Test default 'dict' class magic methods
      """
      
      self.assertEqual(len(self.settings), 20)
      self.assertTrue('user.dbpath' in self.settings)
      self.assertFalse('dbpath' in self.settings)
      self.assertIsNotNone(self.settings)
      
      subset = self.settings.lie_db
      subset2 = self.settings.lie_logging
      self.assertEqual(subset, subset)
      self.assertNotEqual(self.settings, subset)
      self.assertGreater(self.settings, subset)
      self.assertGreaterEqual(subset2, subset)
      self.assertLess(subset, self.settings)
      self.assertLessEqual(subset, subset2)
      
    def test_config_search(self):
      """
      Test config dictionary search by fnmatch Unix style wildcard use
      or regular expressions.
      """
      
      # fnmatch wildcard search
      self.assertEqual(len(self.settings.search('lie_db.*')), 7)
      self.assertEqual(len(self.settings.search('*PrintingObserver*')), 5)
      
      # regular expression search
      self.assertEqual(len(self.settings.search('^lie_db', regex=True)), 7)
    
    def test_config_dict_methods(self):
      """
      Test default dictionary key/value/item methods
      """
      
      self.assertEqual(sorted(self.settings.keys()), sorted(self.data.keys()))
      self.assertEqual(len([True for i in self.settings.values() if i in formatted_example_config.values()]), 20)
      
      if PY3:
        self.assertCountEqual(self.settings.items(), formatted_example_config.items())
      else:
        self.assertItemsEqual(self.settings.items(), formatted_example_config.items())
        
      self.assertDictEqual(self.settings.dict(), formatted_example_config)
    
    def test_config_specialmethods(self):
      """
      Test methods special to the config class (not dict related)
      """
      
      self.assertTrue(self.settings.isnested)
      
      sub = self.settings.subdict(['lie_db.dblog','system.port','user.dbpath'])
      self.assertIsNotNone(sub)
      self.assertIsInstance(sub, ConfigHandler)
      self.assertEqual(len(sub), 3)
      self.assertEqual(sub.user.dbpath, '/usr/app/data/user')
      
      self.assertListEqual(self.settings.get_attributes_at_level(),
        ['lie_db', 'lie_logging', 'system', 'user'])
      
    def test_config_itemaccess(self):
      
      # __getitem__ access
      self.assertEqual(self.settings['lie_db.port'], 27017)
      self.assertRaises(KeyError, lambda:  self.settings['port'])
      
      # __getattr__ access
      self.assertEqual(self.settings.lie_db.port, 27017)
      subset = self.settings.lie_db
      self.assertIsInstance(subset, ConfigHandler)
      
      # dictionary get access
      self.assertIsNone(self.settings.get('key_not_available'))
    
    def test_config_attribute_overload(self):
      """
      Test attribute overloading with attribute resolution order
      """
      
      subset = self.settings.search(['^lie_db','^system'], regex=True)
      
      self.assertEqual(subset.flatten().port, 50000)
      self.assertEqual(subset.flatten(resolve_order=['system','lie_db']).port, 27017)

    def test_config_update(self):
      """
      Test dictionary set, remove and update methods
      """
      
      subset = self.settings.lie_db
      subset2 = self.settings.lie_logging
      
      # When the config instance is not frozen
      self.settings['lie_db.host'] = 'host1'
      self.assertEqual(self.settings.get('lie_db.host'), 'host1')
      self.settings.lie_db.host = 'host2'
      self.assertEqual(self.settings.get('lie_db.host'), 'host2')
      self.settings.set('lie_db.host', 'localhost')
      self.assertEqual(self.settings.get('lie_db.host'), 'localhost')
      
      rawdict = subset.dict()
      rawdict.update(subset2.dict())
      subset.update(subset2)
      self.assertDictEqual(subset.dict(), rawdict)
      subset.remove('PrintingObserver.activate')
      self.assertNotIn('PrintingObserver.activate', subset)
      subset.PrintingObserver.remove('datefmt')
      self.assertNotIn('PrintingObserver.datefmt', subset)
      
      del subset['terminate_mongod_on_exit']
      self.assertNotIn('terminate_mongod_on_exit', subset)
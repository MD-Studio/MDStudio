# -*- coding: utf-8 -*-

"""
file: test.py

Unit tests for the lie_config component
"""

import os
import sys
import unittest
import json
import copy

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

# Get the Python version as some unittests differ between
# Python 2.x and 3.x
PY3 = sys.version_info.major == 3

from lie_config import *
from lie_config.config_io import _flatten_nested_dict, config_from_json

formatted_example_config = {
    'entry1_level1.param1': '/usr/app/data/liedb',
    'entry1_level1.param2': 'liestudio',
    'entry1_level1.param3': 100,
    'entry1_level1.param4': 12.45,
    'entry1_level1.param5': True,
    'entry1_level1.param6': '%m/%d/%Y %I:%M:%S',
    'entry1_level1.param7': u'ইউনিকোড কী?',
    'entry2_level1.level2.param1': True,
    'entry2_level1.level2.param2': '%m/%d/%Y %I:%M:%S',
    'entry2_level1.level2.param3': '{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n',
    'entry2_level1.level2.param4.log_level': 'debug',
    'entry2_level1.level2.param4.app_namespace': ' > 5',
    'entry2_level1.level2_1.param1': False,
    'entry2_level1.level2_1.param2': '%m/%d/%Y %I:%M:%S',
    'entry2_level1.level2_1.param3': '{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n',
    'entry2_level1.level2_1.param4.app_namespace': ' > 3',
    'entry2_level1.level2_1.param4.log_level': 'infp',
    'entry3_level1.param1': '/usr/app',
    'entry3_level1.param2': 5000,
    'entry3_level1.param3': 'SYSTEM_STATUS',
    'entry4_level1.param1': '/usr/app/data/user'
}


class ConfigHandlerTests(unittest.TestCase):
    """
    Unittest ConfigHandler class
    """

    _currpath = os.path.abspath(__file__)
    _settings_json = os.path.join(os.path.dirname(_currpath), '../', 'files', 'config_handler_test.json')

    def setUp(self):
        """
        ConfigHandlerTests class setup

        Load test settings file from config_handler_test.json
        """

        self.data = _flatten_nested_dict(json.load(open(self._settings_json)))
        self.settings = ConfigHandler()
        self.settings.load(self.data)

    def test_config_magicmethod(self):
        """
        Test truth testing magic methods.
        """

        self.assertEqual(len(self.settings), 21)
        self.assertTrue('entry1_level1.param1' in self.settings)
        self.assertFalse('param1' in self.settings)
        self.assertIsNotNone(self.settings)

        subset = self.settings.entry1_level1
        subset2 = self.settings.entry2_level1
        self.assertEqual(subset, subset)
        self.assertNotEqual(self.settings, subset)
        self.assertGreater(self.settings, subset)
        self.assertGreaterEqual(subset2, subset)
        self.assertLess(subset, self.settings)
        self.assertLessEqual(subset, subset2)

    def test_config_addition(self):
        """
        Test addition of ConfigHandeler objects
        """

        # Test addition using magic method, add unique keys in
        # other to self
        subset = copy.deepcopy(self.settings.entry3_level1)
        subset2 = copy.deepcopy(self.settings.entry4_level1)
        addition = subset + subset2
        self.assertNotEqual(id(addition), id(subset))
        self.assertEqual(addition.keys(), [u'param3', u'param2', u'param1'])
        self.assertEqual(addition.values(), [u'SYSTEM_STATUS', 5000, u'/usr/app'])

        # Test inplace addition using magic method, add unique keys
        # in other to self
        subset = copy.deepcopy(self.settings.entry3_level1)
        subset2 = copy.deepcopy(self.settings.entry4_level1)
        subset += subset2
        self.assertEqual(subset.keys(), [u'param3', u'param2', u'param1'])
        self.assertEqual(subset.values(), [u'SYSTEM_STATUS', 5000, u'/usr/app'])

    def test_config_subtraction(self):
        """
        Test subtraction of ConfigHandeler objects
        """

        # Make subdict of entry2 and entry3 keys. Then subtract entry 3 again
        # using magic method
        subset = copy.deepcopy(self.settings.search(['entry2_level1*', 'entry3_level1*']))
        subtract = subset - self.settings.entry3_level1
        self.assertEqual(subtract.keys(), [u'entry2_level1.level2.param4.app_namespace',
                                           u'entry2_level1.level2.param1', u'entry2_level1.level2.param2',
                                           u'entry2_level1.level2.param3', u'entry2_level1.level2_1.param4.log_level',
                                           u'entry2_level1.level2_1.param3', u'entry2_level1.level2_1.param2',
                                           u'entry2_level1.level2.param4.log_level', u'entry2_level1.level2_1.param1',
                                           u'entry2_level1.level2_1.param4.app_namespace'])

        # Make subdict of entry2 and entry3 keys. Then subtract entry 3 again
        # using inplace magic method
        subset = copy.deepcopy(self.settings.search(['entry2_level1*', 'entry3_level1*']))
        subset -= self.settings.entry3_level1
        self.assertEqual(subset.keys(), [u'entry2_level1.level2.param4.app_namespace',
                                         u'entry2_level1.level2.param1', u'entry2_level1.level2.param2',
                                         u'entry2_level1.level2.param3', u'entry2_level1.level2_1.param4.log_level',
                                         u'entry2_level1.level2_1.param3', u'entry2_level1.level2_1.param2',
                                         u'entry2_level1.level2.param4.log_level', u'entry2_level1.level2_1.param1',
                                         u'entry2_level1.level2_1.param4.app_namespace'])

    def test_config_update(self):
        """
        Test ConfigHandler update method
        """

        # Test update, add and replace keys in self with other
        subset = copy.deepcopy(self.settings.entry3_level1)
        subset2 = copy.deepcopy(self.settings.entry4_level1)
        subset.update(subset2)
        self.assertEqual(subset.keys(), [u'param3', u'param2', u'param1'])
        self.assertEqual(subset.values(), [u'SYSTEM_STATUS', 5000, u'/usr/app/data/user'])

    def test_config_search(self):
        """
        Test config dictionary search by fnmatch Unix style wildcard use
        or regular expressions.
        """

        # fnmatch wildcard search
        self.assertEqual(len(self.settings.search('entry1_level1.*')), 7)
        self.assertEqual(len(self.settings.search('*level2_1*')), 5)

        # regular expression search
        self.assertEqual(len(self.settings.search('^entry1_level1', regex=True)), 7)

    def test_config_dict_methods(self):
        """
        Test default dictionary key/value/item methods
        """

        self.assertEqual(sorted(self.settings.keys()), sorted(self.data.keys()))
        self.assertEqual(len([True for i in self.settings.values() if i in formatted_example_config.values()]), 21)

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

        sub = self.settings.subdict(['entry1_level1.param1', 'entry3_level1.param2', 'entry4_level1.param1'])
        self.assertIsNotNone(sub)
        self.assertIsInstance(sub, ConfigHandler)
        self.assertEqual(len(sub), 3)
        self.assertEqual(sub.entry4_level1.param1, '/usr/app/data/user')

        self.assertListEqual(self.settings.get_attributes_at_level(),
                             ['entry1_level1', 'entry2_level1', 'entry3_level1', 'entry4_level1'])

    def test_config_itemaccess(self):
        """
        Test getter/setter methods
        """

        # __getitem__ access
        self.assertEqual(self.settings['entry1_level1.param3'], 100)
        self.assertRaises(KeyError, lambda:  self.settings['param3'])

        # __getattr__ access
        self.assertEqual(self.settings.entry1_level1.param3, 100)
        subset = self.settings.entry1_level1
        self.assertIsInstance(subset, ConfigHandler)

        # dictionary get access
        self.assertIsNone(self.settings.get('key_not_available'))

        # When the config instance is not frozen
        self.settings['entry1_level1.param2'] = 200
        self.assertEqual(self.settings.get('entry1_level1.param2'), 200)
        self.settings.entry1_level1.param2 = 300
        self.assertEqual(self.settings.get('entry1_level1.param2'), 300)
        self.settings.set('entry1_level1.param2', "liestudio")
        self.assertEqual(self.settings.get('entry1_level1.param2'), "liestudio")

    def test_config_attribute_overload(self):
        """
        Test attribute overloading with attribute resolution order
        """

        subset = self.settings.search(['^entry1_level1', '^entry3_level1'], regex=True)

        self.assertEqual(subset.flatten().param4, 12.45)
        self.assertEqual(subset.flatten(resolve_order=['entry3_level1', 'entry1_level1']).param2, 'liestudio')

    def test_config_removal(self):
        """
        Test dictionary removal operations.
        Make a deepcopy of subdicts before removing items
        """

        # param5 only occurs once
        subset = copy.deepcopy(self.settings.entry1_level1)
        subset.remove('param5')
        self.assertNotIn('param5', subset)

        # log_level occurs twice at differently named levels
        subset2 = copy.deepcopy(self.settings.entry2_level1)
        subset2.remove('level2.param4.log_level')
        subset2.level2_1.param4.remove('app_namespace')
        self.assertNotIn('level2.param4.log_level', subset2)
        self.assertNotIn('level2_1.param4.app_namespace', subset2)

        # Difference between a frozen and unfrozen dict
        self.assertFalse('entry2_level1.level2_1.param4.app_namespace' in subset2._config)
        subset2._freeze = True
        subset2.remove('level2_1.param2')
        self.assertTrue('entry2_level1.level2_1.param2' in subset2._config)

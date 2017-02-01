# -*- coding: utf-8 -*-

import json
import os
import copy
import sys
import unittest

# This seems to be needed to get utf-8 encoding working properly
reload(sys)
sys.setdefaultencoding('utf8')

# Get the Python version as some unittests differ between
# Python 2.x and 3.x
PY3 = sys.version_info.major == 3

from   config_graph import ConfigHandler
from   graph_algorithms import *

DICT1 = {u'level2.param1': True, u'level2_1.param4.app_namespace': u' > 3', u'level2_1.param1': False, u'level2_1.param2': u'%m/%d/%Y %I:%M:%S', u'level2_1.param3': u'{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n', u'level2_1.param4.log_level': u'infp', u'level2.param2': u'%m/%d/%Y %I:%M:%S', u'level2.param3': u'{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n', u'level2.param4.log_level': u'debug', u'level2.param4.app_namespace': u' > 5'}
DICT2 = {u'entry3_level1.param1': u'/usr/app', u'entry3_level1.param2': 5000, u'entry3_level1.param3': u'SYSTEM_STATUS'}
DICT3 = {u'entry3_level1': {u'param3': u'SYSTEM_STATUS', u'param2': 5000, u'param1': u'/usr/app'}}

class ConfigHandlerTests(unittest.TestCase):
    """
    Unittest ConfigHandler class
    """
    
    _currpath = os.path.abspath(__file__)
    _settings_json = os.path.join(os.path.dirname(_currpath), 'config_handler_test.json')
    
    def setUp(self):
        """
        ConfigHandlerTests class setup
        
        Load test settings file from config_handler_test.json
        """
        
        self.data = json.load(open(self._settings_json))
        self.settings = ConfigHandler()
        self.settings.load(self.data)
    
    def test_config_dict_keys(self):
        """
        Test default dictionary keys method
        """
        
        sub = self.settings.getnodes(1)
        self.assertEqual(list(self.settings.keys()), [u'entry3_level1', u'entry4_level1', u'entry1_level1', u'entry2_level1'])
        self.assertEqual([k.key() for k in self.settings], [u'entry3_level1', u'entry4_level1', u'entry1_level1', u'entry2_level1'])
        self.assertEqual(list(sub.keys()), [u'param3', u'param2', u'param1'])
        
    def test_config_dict_values(self):
        """
        Test default dictionary values method
        """
        
        leaf_selection = self.settings.getnodes(1)
        self.assertEqual(list(leaf_selection.values()), [u'SYSTEM_STATUS', 5000, u'/usr/app'])
        self.assertEqual(len([n for n in self.settings.values() if isinstance(n, ConfigHandler)]), 4)
    
    def test_config_dict_items(self):
        """
        Test default dictionary items method
        """
        
        nids = []
        for key,node in self.settings.items(): 
            self.assertIsInstance(node, ConfigHandler)
            nids.append(node.nid)
        self.assertEqual(nids, [1,5,7,15])
    
    def test_config_dict_get(self):
        """
        Test default dictionary get method
        """
        
        get = self.settings.get('entry3_level1')
        self.assertEqual(get.nid, 1)
    
    def test_config_dict_subdict(self):
        
        sub = self.settings.descendant(15)
        
        self.assertDictEqual(self.settings.getnodes(sub).dict(), DICT1)
        self.assertDictEqual(self.settings.getnodes(1).dict(), DICT2)
        self.assertDictEqual(self.settings.getnodes(1)(), DICT3)
    
    def test_config_dict_magicmethods(self):
        """
        Test class magic methods
        """
        
        # Truth testing magic methods
        self.assertEqual(len(self.settings), 4)
        self.assertIsNotNone(self.settings)
        
        subset = self.settings.entry1_level1
        subset2 = self.settings.entry2_level1
        self.assertEqual(subset, subset)
        self.assertNotEqual(self.settings, subset)
        self.assertGreater(subset, self.settings)
        self.assertGreaterEqual(subset, self.settings)
        self.assertLess(self.settings, subset)
        self.assertLessEqual(subset2, subset)
        
        # key based contains
        self.assertTrue('entry3_level1' in self.settings)
        self.assertFalse('unknown_key' in self.settings)
        self.assertTrue('level2_1' in self.settings.get('entry2_level1'))
        self.assertIsNone(self.settings.get('key_not_available'))
        
        sub = self.settings.getnodes([7,16,17])
        self.assertTrue('level2_1', sub)
        
        # __getattr__ access
        self.assertEqual(self.settings.entry1_level1.param3.value(), 100)
        subset = self.settings.entry1_level1
        self.assertIsInstance(subset, ConfigHandler)
        
        # __setitem__ 
        self.settings['entry1_level1.param2'] = 200
        self.assertEqual(self.settings.get('.entry1_level1.param2').value(), 200)
        self.settings.entry1_level1.param2 = 300
        self.assertEqual(self.settings.get('.entry1_level1.param2').value(), 300)
        self.settings.set('entry1_level1.param2', "liestudio")
        self.assertEqual(self.settings.get('.entry1_level1.param2').value(), "liestudio")
    
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
        self.assertEqual(list(addition.keys()), [u'param3', u'param2', u'param1'])
        self.assertEqual(list(addition.values()), [u'SYSTEM_STATUS', 5000, u'/usr/app'])
        
        # Test inplace addition using magic method, add unique keys
        # in other to self
        subset = copy.deepcopy(self.settings.entry3_level1)
        subset2 = copy.deepcopy(self.settings.entry4_level1)
        subset += subset2
        self.assertEqual(list(subset.keys()), [u'param3', u'param2', u'param1'])
        self.assertEqual(list(subset.values()), [u'SYSTEM_STATUS', 5000, u'/usr/app'])
    
    def test_config_subtraction(self):
        """
        Test subtraction of ConfigHandeler objects
        """
        
        # Make subdict of entry2 and entry3 keys. Then subtract entry 3 again
        # using magic method
        subset = copy.deepcopy(self.settings.find(['.entry2_level1','.entry3_level1'])))
        print(subset)
        subtract = subset - self.settings.entry3_level1
        self.assertEqual(subtract.keys(), [u'entry2_level1.level2.param4.app_namespace', 
            u'entry2_level1.level2.param1', u'entry2_level1.level2.param2', 
            u'entry2_level1.level2.param3', u'entry2_level1.level2_1.param4.log_level',
            u'entry2_level1.level2_1.param3', u'entry2_level1.level2_1.param2',
            u'entry2_level1.level2.param4.log_level', u'entry2_level1.level2_1.param1',
            u'entry2_level1.level2_1.param4.app_namespace'])
        
        # Make subdict of entry2 and entry3 keys. Then subtract entry 3 again
        # using inplace magic method
        subset = copy.deepcopy(self.settings.search(['entry2_level1*','entry3_level1*']))
        subset -= self.settings.entry3_level1
        self.assertEqual(subset.keys(), [u'entry2_level1.level2.param4.app_namespace', 
            u'entry2_level1.level2.param1', u'entry2_level1.level2.param2', 
            u'entry2_level1.level2.param3', u'entry2_level1.level2_1.param4.log_level',
            u'entry2_level1.level2_1.param3', u'entry2_level1.level2_1.param2',
            u'entry2_level1.level2.param4.log_level', u'entry2_level1.level2_1.param1',
            u'entry2_level1.level2_1.param4.app_namespace'])
    
    def test_config_dict_specialmethods(self):
        """
        Test non-dictionary style class methods
        """
        
        # key based contains that works on any level
        self.assertTrue(self.settings.contains('entry4_level1'))
        self.assertTrue(self.settings.contains('config'))
        self.assertTrue(self.settings.contains('param7'))
        self.assertFalse(self.settings.contains('param11'))
        
        sub = self.settings.getnodes([7,16,17])
        self.assertFalse(sub.contains('param11'))
        self.assertTrue(sub.contains('level2_1'))
        
        # Searching for nodes using XPath like query language
        self.assertEqual(self.settings.find('.entry1_level1.param2'), [13])
        self.assertEqual(self.settings.find('..param2'), [3,13,21,28])
        
        
if __name__ == '__main__':
    unittest.main(verbosity=2)
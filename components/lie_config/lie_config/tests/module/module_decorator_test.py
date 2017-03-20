# -*- coding: utf-8 -*-

"""
file: decorator_test.py

Unit tests for the lie_config component
"""

import os
import json
import sys
import unittest2

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

from   lie_config import get_config


class ConfigDecoratorTests(unittest2.TestCase):
    """
    Unittest the configuration decorator method
    """
    
    _currpath = os.path.abspath(__file__)
    _settings_json = os.path.join(os.path.dirname(_currpath), 'files', 'config_decorator_test.json')
    
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
        
        from decorator_test import decorator_method_defined, change_value_elsewhere
        
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
        
        from decorator_test import decorator_method_undefined
        
        self.assertEqual(decorator_method_undefined(2), (2,4))
    
    def test_single_function_decorator_with_kwargs(self):
        """
        Test the decorator on a single function that also accepts
        additonal kyword arguments via **kwargs.
        This should result in the decorator passing all keyword
        arguments available for the function.
        """
        
        from decorator_test import decorator_method_withkwargs
        
        self.assertEqual(decorator_method_withkwargs(2), (4, 6, {'nested': {'sec': True}, 'other': 'additional'}))
    
    def test_single_function_decorator_resolutionorder(self):
        """
        Test the decorator on a single function with a predefined
        ConfigHandler instance.
        The decorator is configured to resolve the function arguments
        in predefined overload order.
        """
        
        from decorator_test import decorator_method_resolutionorder
        
        self.assertEqual(decorator_method_resolutionorder(2), (20,6))
    
    def test_class_decorator(self):
        """
        Test the decorator on a class with a predefined ConfigHandler
        instance.
        """
        
        from decorator_test import decorator_class
        
        klass = decorator_class()
        self.assertEqual(klass.run(2), (4,6))
        self.assertEqual(klass.decorated_run(2), (20,30))
# -*- coding: utf-8 -*-

"""
Python function for lie_docking module and WAMP API unit tests, run as:
::
    test = module_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test)

    test = wamp_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test)

This will run both the module functionality tests and the WAMP API tests.
A running instance of the Crossbar WAMP router is required for the WAMP
API unit tests. 
A basic Crossbar router configuration for this purpose is shipped within
the `tests` directory and should be launched as:
::
    crossbar start --cbdir tests/unittest_crossbar
"""

import unittest

import tests.module_test
import tests.wamp_api_test

def module_test_suite():
    """
    Run lie_docking module unit tests
    """
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(tests.module_test)
    return suite

def wamp_test_suite():
    """
    Run lie_docking WAMP API unit tests
    """
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(tests.wamp_api_test)
    return suite
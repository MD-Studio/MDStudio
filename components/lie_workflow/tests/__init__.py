# -*- coding: utf-8 -*-

"""
Python function for lie_workflow module, run as:
::
    test = module_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test)
"""

import os
import unittest2
import logging

# Init basic logging
logging.basicConfig(level=logging.DEBUG)

def module_test_suite():
    """
    Run lie_workflow module unit tests
    """
    
    loader = unittest2.TestLoader()
    suite = loader.discover(os.path.dirname(__file__), pattern='module_*.py')
    return suite
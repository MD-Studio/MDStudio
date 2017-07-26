# -*- coding: utf-8 -*-

"""
Python function for lie_graph module, run as:
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
    Run lie_graph module unit tests
    """
    
    testpath = os.path.join(os.path.dirname(__file__), 'module')
    loader = unittest2.TestLoader()
    suite = loader.discover(testpath, pattern='graph_*.py')
    return suite

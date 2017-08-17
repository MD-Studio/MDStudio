# -*- coding: utf-8 -*-

"""
Python runner for lie_structures module unit tests, run as:
::
    python tests
"""

import os
import unittest2
import logging

# Init basic logging
logging.basicConfig(level=logging.DEBUG)

def module_test_suite():
    """
    Run lie_structures module unit tests
    """
    loader = unittest2.TestLoader()
    
    print('Running lie_structures unittests')
    testpath = os.path.join(os.path.dirname(__file__), 'module')
    suite = loader.discover(testpath, pattern='module_*_test.py')
    runner = unittest2.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    
    module_test_suite()
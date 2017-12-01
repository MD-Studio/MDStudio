# -*- coding: utf-8 -*-

"""
Python unit test for lie_haddock module, run as:
::
    test = module_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test)
"""

import os
import unittest2


def module_test_suite():
    """
    Run lie_haddock module unit tests
    """

    loader = unittest2.TestLoader()
    suite = loader.discover(os.path.dirname(__file__), pattern='module_*.py')
    return suite

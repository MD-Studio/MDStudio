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


def module_test_suite():
    """
    Run lie_config module unit tests
    """

    loader = unittest2.TestLoader()
    suite = loader.discover(os.path.dirname(__file__), pattern='module_*.py')
    return suite

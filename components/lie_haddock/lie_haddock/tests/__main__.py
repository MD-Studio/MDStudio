# -*- coding: utf-8 -*-

"""
Python runner for lie_haddock module unit tests, run as:
::
    python tests
"""

import os
import unittest2


def module_test_suite():
    """
    Run lie_haddock module unit tests
    """
    loader = unittest2.TestLoader()

    print('Running lie_haddock unittests')
    searchpath = os.path.join(os.path.dirname(__file__), 'module/')
    suite = loader.discover(searchpath, pattern='module_*.py')
    runner = unittest2.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    module_test_suite()

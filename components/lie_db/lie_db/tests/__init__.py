from __future__ import absolute_import
import os
import unittest2

currpath = os.path.dirname(__file__)


def wamp_test_suite():
    """
    Run lie_docking WAMP API unit tests
    """

    loader = unittest2.TestLoader()
    suite = loader.discover(currpath, pattern='wamp_*.py',  top_level_dir=currpath)
    return suite

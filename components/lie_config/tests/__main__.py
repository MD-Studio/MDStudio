# -*- coding: utf-8 -*-

"""
Python runner for lie_config module unit tests, run as:
::
    python tests

This will run both the module functionality tests and the WAMP API tests.
A running instance of the Crossbar WAMP router is required for the WAMP
API unit tests. 
A basic Crossbar router configuration for this purpose is shipped within
the `tests` directory and should be launched as:
::
    crossbar start --cbdir tests/unittest_crossbar

Optionally the module unit tests can be skipped using the '-m' and the 
WAMP API unit tests can be skipped using the '-w' command line argument to
tests.
"""

import argparse
import os
import unittest2

def module_test_suite(args):
    """
    Run lie_config module and WAMP API unit tests
    
    :param args: command line arguments
    :type args:  argparse parser object
    """
    
    loader = unittest2.TestLoader()
    currpath = os.path.dirname(__file__)

    if not args.no_module:
        print('Running lie_config unittests')
        suite = loader.discover(currpath, pattern='module_*.py')
        runner = unittest2.TextTestRunner(verbosity=2)
        runner.run(suite)
    
    if not args.no_wamp:
        print('Running lie_config WAMP API test')
        suite = loader.discover(currpath, pattern='wamp_*.py')
        runner = unittest2.TextTestRunner(verbosity=2)
        runner.run(suite)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog='tests', usage='%(prog)s [options]')
    parser.add_argument('-m', '--no_module_tests', dest='no_module', action="store_true",
                     help='Skip module unit tests')
    parser.add_argument('-w', '--no_wamp_tests', dest='no_wamp', action="store_true",
                     help='Skip module WAMP API unit tests')
    args = parser.parse_args()
    
    module_test_suite(args)
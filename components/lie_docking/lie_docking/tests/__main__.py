# -*- coding: utf-8 -*-

"""
Python runner for lie_docking module unit tests, run as:
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

import unittest2
import argparse

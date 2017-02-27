# -*- coding: utf-8 -*-

"""
Python function for lie_config module and WAMP API unit tests, run as:
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

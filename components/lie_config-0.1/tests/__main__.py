import unittest

import tests.module_test
import tests.wamp_api_test

def module_test_suite():
    
    print('Running lie_config unittests')
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(tests.module_test)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    
    print('Running lie_config WAMP API test')
    # suite = loader.loadTestsFromModule(tests.wamp_api_test)
    # runner = unittest.TextTestRunner(verbosity=2)
    # runner.run(suite)
    
if __name__ == '__main__':
    module_test_suite()
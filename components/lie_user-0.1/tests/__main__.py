import unittest
import tests.module_test

def module_test_suite():
    
    print('Running lie_user unittests')
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(tests.module_test)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    
if __name__ == '__main__':
    module_test_suite()
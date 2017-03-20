import unittest
import tests.module_test

def module_test_suite():
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(tests.module_test)
    return suite
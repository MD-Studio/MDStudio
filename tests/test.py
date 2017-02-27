from __future__ import absolute_import

import imp
import os
import re
from glob import glob

import unittest2

__rootpath__  = os.path.dirname(os.path.abspath(__file__))

def list_components_tests(search_path):
    found = {}
    for g in glob(os.path.join(search_path, '*/*/')):
        match = re.match(r'(.*/(.*)-.*/tests)/', g)
        if match:
            found['{}.tests'.format(match.group(2))] =  os.path.normpath(match.group(1))
    return found

def loadTests(suite, loader, dir, type):
    if os.path.isdir(os.path.join(dir, type)):
        tests = loader.discover(os.path.join(dir, type), "*.py", dir)
        suite.addTests(tests)
    return None

# Add all tests.
alltests = unittest2.TestSuite()
for name, path in list_components_tests(os.path.join(__rootpath__, '../components/')).items():
    print("Loading '{}' from '{}'".format(name, path))
    loader = unittest2.TestLoader()

    loadTests(alltests, loader, path, "module")
    #loadTests(alltests, loader, path, "wamp")

result = unittest2.TextTestRunner(verbosity=2).run(alltests)
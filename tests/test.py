from __future__ import absolute_import

import imp
import os
import re
from glob import glob

import sys
import unittest2

__root_path__ = os.path.dirname(os.path.abspath(__file__))


def list_components_tests(search_path):
    found = {}
    for g in glob(os.path.join(search_path, '*/*/tests')):
        match = re.match(r'(.*/.*/(.*))/tests', g)
        if match:
            found['{}_tests'.format(match.group(2))] = os.path.normpath(match.group(1))
    return found


def load_studio_tests(suite, loader, dir, type):
    if os.path.isdir(os.path.realpath(os.path.join(dir, type))):
        start_dir = os.path.realpath(os.path.join(dir, type))
        top_level_dir = os.path.realpath(os.path.join(dir, '../'))
        tests = loader.discover(start_dir, "*.py", top_level_dir)
        suite.addTests(tests)

#def main():
search_path = os.path.join(__root_path__, '../components/')

for g in glob(os.path.join(search_path, '*/')):
    sys.path.append(os.path.realpath(os.path.join(g, '../')))


# Add all tests.
alltests = unittest2.TestSuite()
for name, path in list_components_tests(search_path).items():
    print("Loading '{}' from '{}'".format(name, path))
    if name == "lie_user_tests" or name == "lie_config_tests":
        loader = unittest2.TestLoader()

        load_studio_tests(alltests, loader, path, "tests/module/")
        # loadTests(alltests, loader, path, "wamp")

result = unittest2.TextTestRunner(verbosity=2).run(alltests)


#if __name__ == '__main__':
#    main()
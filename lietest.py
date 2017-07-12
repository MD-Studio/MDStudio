from __future__ import absolute_import

import sys
from glob import glob

import os
import re
import unittest2


def list_components_tests(search_path):
    found = {}
    for g in glob(os.path.join(search_path, '*/*/tests')):
        match = re.match(r'(.*/.*/(.*))/tests', g)
        if match:
            found['{}_tests'.format(match.group(2))] = os.path.normpath(match.group(1))
    return found


def load_studio_tests(suite, loader, cdir, ctype):
    if os.path.isdir(os.path.realpath(os.path.join(cdir, ctype))):
        start_dir = os.path.realpath(os.path.join(cdir, ctype))
        top_level_dir = os.path.realpath(os.path.join(cdir, '../'))
        tests = loader.discover(start_dir, "*_test.py", top_level_dir)
        if tests:
            suite.addTests(tests)


# noinspection PyUnusedLocal
def load_tests(loader, tests, pattern):
    root_path = os.path.dirname(os.path.abspath(__file__))
    search_path = os.path.join(root_path, 'components/')

    for g in glob(os.path.join(search_path, '*/')):
        sys.path.append(os.path.realpath(g))

    # Add all tests.
    all_tests = unittest2.TestSuite()
    for name, path in list_components_tests(search_path).items():
        print("Loading '{}' from '{}'".format(name, path))
        load_studio_tests(all_tests, loader, path, "tests/module/")

    return all_tests


if __name__ == '__main__':
    unittest2.main(verbosity=2)

# -*- coding: utf-8 -*-

"""
file: test.py

Unit tests for the lie_config component
"""

import os
import sys
import unittest
import getpass
import json

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

# Get the Python version as some unittests differ between
# Python 2.x and 3.x
PY3 = sys.version_info.major == 3

from lie_system import *
from lie_config.config_io import config_from_json
from lie_system.wamp_schema import liestudio_task_schema

class LieWampTaskMetadataTest(unittest.TestCase):

    _currpath = os.path.abspath(__file__)

    def test_task_default_metadata(self):
        """
        Test default WAMP task metadata generation
        """

        metadata = WAMPTaskMetaData()
        required = liestudio_task_schema['required']

        self.assertItemsEqual(metadata.dict().keys(), required)
        self.assertEqual(metadata.system_user, getpass.getuser())

    def test_task_default_fromjson(self):

        jsonmeta = json.load(open(os.path.join(self._currpath, 'default_task_metadata.json')))
        metadata = WAMPTaskMetaData(metadata=jsonmeta)

    def test_task_prefilled_fromjson(self):

        jsonmeta = json.load(open(os.path.join(self._currpath, 'prefilled_task_metadata.json')))
        metadata = WAMPTaskMetaData()
        metadata['authmethod'] = 'ticket'

    def test_task_metadata_setter(self):

        metadata = WAMPTaskMetaData()

        # Test option based attributes
        failed = False
        try:
            metadata.status = 'hello'
        except LookupError:
            failed = True

        self.assertTrue(failed)
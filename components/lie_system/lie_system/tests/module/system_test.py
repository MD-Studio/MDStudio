# -*- coding: utf-8 -*-

"""
file: test.py

Unit tests for the lie_config component
"""

import os
import sys
import unittest
import json
import copy
import glob

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

# Get the Python version as some unittests differ between
# Python 2.x and 3.x
PY3 = sys.version_info.major == 3

from lie_system import *
from lie_config.config_io import config_from_json


class LieWampTaskTest(unittest.TestCase):
    """
    Unittest system WAMP messaging
    """

    _currpath = os.path.abspath(__file__)
    _settings_json = os.path.join(os.path.dirname(_currpath), '../system_wamp_test.json')

    def setUp(self):
        """
        SystemWAMPmessagingTest class setup

        Load test settings file from system_wamp_test.json
        """

        self.data = config_from_json(self._settings_json)
        #self.settings = LieWampTask()

    def test_task_setup(self):

        # Empty Task
        # print(self.settings)

        # Loading a predefined task
        # self.settings.load(self.data)
        # self.settings._validate()

        # Get _wampTask in _inputDict
        #_inputDict = self.settings._inputDict.ligandFile._wampTask

        # self.settings._resolve_config_level()
        # print(self.settings)
        pass

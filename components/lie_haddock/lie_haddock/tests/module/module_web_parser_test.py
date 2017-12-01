# -*- coding: utf-8 -*-

"""
file: haddock_web_parser_test.py

Unit tests for the haddock .web file format parser
"""

import os
import sys
import unittest2
import jsonschema
import json

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

from lie_haddock.haddock_web_parser import HaddockParamWeb

class TestGraph(unittest2.TestCase):

    _param = os.path.join(currpath, '../', 'files', 'haddockparam.web')
    _schema = os.path.join(currpath, '../../', 'haddock_schema.json')
    
    def setUp(self):
        """
        ConfigHandlerTests class setup

        Load graph from graph.tgf file
        """

        self.params = HaddockParamWeb(self._param)
    
    def test_param_validate(self):
        
        param = json.load(open(os.path.join(currpath, '../', 'files', 'test.json')))
        schema = json.load(open(self._schema))
        
        jsonschema.validate(param, schema)

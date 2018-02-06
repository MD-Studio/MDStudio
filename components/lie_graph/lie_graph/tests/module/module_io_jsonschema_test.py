# -*- coding: utf-8 -*-

"""
file: graph_io_jsonschema_test.py

Unit tests for jsonschema import as graph object
"""

import json
import os
import unittest2

from lie_graph.graph_io.io_jsonschema_format import JSONSchemaParser
from lie_graph.graph_io.io_dict_parser import graph_to_dict


class JSONSchemaParserTests(unittest2.TestCase):

    currpath = os.path.dirname(__file__)

    def test_jsonschema_import(self):
        """
        Test import of JSON schema
        """

        schema = os.path.abspath(os.path.join(self.currpath, '../files/jsonschema1.json',))
        parser = JSONSchemaParser(schema)

        for e in parser.graph:
            print(e.data, e.value, e.nid)

        # Setting wrong type should raise error
        d = parser.graph.query_nodes({'data': 'dtend'})
        self.assertRaises(ValueError, d.set, 'data', 3)

        # import pprint
        # pp = pprint.PrettyPrinter()
        # pp.pprint(graph_to_dict(parser.graph, keystring='data', valuestring='value'))
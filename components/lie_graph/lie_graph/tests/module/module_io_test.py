# -*- coding: utf-8 -*-

"""
file: module_io_test.py

Unit tests for import and export of graph data formats
"""

import os
import unittest2

from lie_graph import Graph, GraphAxis
from lie_graph.graph_helpers import graph_directionality
from lie_graph.graph_io.io_tgf_format import read_tgf, write_tgf

from lie_graph.graph_io.io_jsonschema_format import JSONSchemaParser
from lie_graph.graph_io.io_dict_parser import graph_to_dict

FILEPATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../files/'))


class TGFParserTest(unittest2.TestCase):
    tempfiles = []

    def tearDown(self):
        """
        tearDown method called after each unittest to cleanup
        the files directory
        """

        for tmp in self.tempfiles:
            if os.path.exists(tmp):
                os.remove(tmp)

    def test_format_import(self):
        """
        Test import of format
        """

        tgf_file = os.path.join(FILEPATH, 'graph.tgf')
        graph = read_tgf(tgf_file)

        # Default graph attributes set
        self.assertEqual(len(graph), 11)
        self.assertEqual(len(graph.edges), 11)
        self.assertEqual(graph.is_directed, False)
        self.assertEqual(graph_directionality(graph), 'directional')
        self.assertEqual(graph.root, None)

        # Because default auto_nid is True, string based node IDs not supported
        self.assertTrue('eleven' not in graph.nodes)
        self.assertTrue(11 in graph.nodes)

    def test_format_export(self):
        """
        Test export of format
        """

        tgf_file = os.path.join(FILEPATH, 'graph.tgf')
        graph = read_tgf(tgf_file)

        # Export graph as TGF to file
        tgf = write_tgf(graph)
        outfile = os.path.join(FILEPATH, 'test_export.tgf')
        with open(outfile, 'w') as otf:
            otf.write(tgf.read())
            self.tempfiles.append(outfile)

        self.assertTrue(os.path.isfile(outfile))

        # Import again and compare source graph
        graph1 = read_tgf(outfile)
        self.assertTrue(graph1 == graph)

    def test_format_custom_import(self):
        """
        Test TGF import with custom Graph instance
        """

        # Graph axis class with custom nid ID's
        graph = GraphAxis()
        graph.auto_nid = False
        graph.is_directed = True

        tgf_file = os.path.join(FILEPATH, 'graph.tgf')
        graph = read_tgf(tgf_file, graph=graph)

        # Custom graph attributes set and string based node IDs supported
        self.assertEqual(len(graph), 11)
        self.assertEqual(len(graph.edges), 11)
        self.assertEqual(graph.is_directed, True)
        self.assertEqual(graph_directionality(graph), 'directional')
        self.assertTrue(isinstance(graph, GraphAxis))
        self.assertTrue('eleven' in graph.nodes)




class JSONSchemaParserTests(unittest2.TestCase):

    def test_jsonschema_import(self):
        """
        Test import of JSON schema
        """

        schema = os.path.join(FILEPATH, 'jsonschema1.json',)
        parser = JSONSchemaParser(schema)
        #
        # for e in parser.graph:
        #     print(e.data, e.value, e.nid)
        #
        # # Setting wrong type should raise error
        # d = parser.graph.query_nodes({'data': 'dtend'})
        # self.assertRaises(ValueError, d.set, 'data', 3)

        # import pprint
        # pp = pprint.PrettyPrinter()
        # pp.pprint(graph_to_dict(parser.graph, keystring='data', valuestring='value'))
# -*- coding: utf-8 -*-

"""
file: module_xpath_test.py

Unit tests for XPath query language support in GraphAxis graphs
"""

import os
import unittest2

from lie_graph.graph_io.io_jgf_format import read_jgf
from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools
from lie_graph.graph_query.query_xpath import XpathExpressionEvaluator


class TestXPathQuery(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create a graph to query
        """

        currpath = os.path.dirname(__file__)
        xpath_example = os.path.join(currpath, '../files/graph_xpath.jgf')

        cls.graph = read_jgf(xpath_example)
        cls.graph.node_tools = NodeAxisTools

    def test_query_selfdesc(self):
        """
        Test basic path based query starting from current element (.)
        """

        xpath = XpathExpressionEvaluator()

        # By default we are at root
        self.assertItemsEqual(xpath.resolve('system', self.graph).nodes.keys(), [1])
        self.assertItemsEqual(xpath.resolve('system/segid/residue', self.graph).nodes.keys(), [3, 10, 21, 28])

        # Start search from other node
        sel = self.graph.getnodes(20)
        self.assertItemsEqual(xpath.resolve('system/segid/residue', sel).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('segid/residue', sel).nodes.keys(), [21, 28])

    def test_query_rootdesc(self):
        """
        Test root down search using /
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('/', self.graph).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('/system', self.graph).nodes.keys(), [1])
        self.assertItemsEqual(xpath.resolve('/system/segid', self.graph).nodes.keys(), [2, 20])
        self.assertItemsEqual(xpath.resolve('/system/segid/residue', self.graph).nodes.keys(), [3, 10, 21, 28])
        self.assertItemsEqual(xpath.resolve('/system//residue', self.graph).nodes.keys(), [3, 10, 21, 28])
        self.assertItemsEqual(xpath.resolve('/system/segid/residue/atom', self.graph).nodes.keys(), [4, 5, 6, 7, 8, 9,
                    11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37])

    def test_query_none_rootdesc(self):
        """
        Test root down search using / from non-root position
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('/segid', self.graph).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('/residue', self.graph).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('/segid/residue', self.graph).nodes.keys(), [])

    def test_query_descendants(self):
        """
        Test descendant search using //
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('//', self.graph).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('//system', self.graph).nodes.keys(), [1])
        self.assertItemsEqual(xpath.resolve('//segid', self.graph).nodes.keys(), [2, 20])
        self.assertItemsEqual(xpath.resolve('//residue', self.graph).nodes.keys(), [3, 10, 21, 28])
        self.assertItemsEqual(xpath.resolve('//atom', self.graph).nodes.keys(), [4, 5, 6, 7, 8, 9, 11, 12, 13, 14,
                           15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37])

    def test_query_wildcards(self):
        """
        Test the use of wildcards in the search
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('//*', self.graph).nodes.keys(), self.graph.nodes.keys())
        self.assertItemsEqual(xpath.resolve('/system/*/residue', self.graph).nodes.keys(), [3, 10, 21, 28])

    def test_query_indexselect(self):
        """
        Test selection of nodes based on index
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('//*[10]', self.graph).nodes.keys(), [11])
        self.assertItemsEqual(xpath.resolve('//residue[3]', self.graph).nodes.keys(), [28])
        self.assertItemsEqual(xpath.resolve('//residue[4]', self.graph).nodes.keys(), []) # Index out of range
        self.assertItemsEqual(xpath.resolve('//residue[3]/atom', self.graph).nodes.keys(), [29, 30, 31, 32, 33, 34,
                                                                                            35, 36, 37])

    def test_query_attribute_filter(self):
        """
        Test selection of nodes with filter on attributes
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('//segid[@value]', self.graph).nodes.keys(), [2, 20])
        self.assertItemsEqual(xpath.resolve('//residue[@extra]', self.graph).nodes.keys(), [21, 28])
        self.assertItemsEqual(xpath.resolve('/system/segid/residue/atom[@elem="H"]', self.graph).nodes.keys(),
                              [9, 19, 27, 37])
        self.assertItemsEqual(xpath.resolve('//segid[@value="A"]/residue[@value=1]', self.graph).nodes.keys(), [3])
        self.assertItemsEqual(xpath.resolve('//atom[@value>620]', self.graph).nodes.keys(), [18, 19, 22, 23, 24, 25,
                               26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37])
        self.assertItemsEqual(xpath.resolve('//atom[@value>620][3]', self.graph).nodes.keys(), [23])
        self.assertItemsEqual(xpath.resolve('//atom[@value<608]', self.graph).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('//atom[@value<=608]', self.graph).nodes.keys(), [4])

        # Select all nodes or all atom nodes with at least one attribute
        sel = self.graph.getnodes(10)
        self.assertItemsEqual(xpath.resolve('//*[@*]', sel).nodes.keys(), [10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        self.assertItemsEqual(xpath.resolve('//atom[@*]', sel).nodes.keys(), [11, 12, 13, 14, 15, 16, 17, 18, 19])

    def test_query_axis_filter(self):
        """
        Test XPath axis based selection syntax
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('//segid/child::residue', self.graph).nodes.keys(), [3, 10, 21, 28])
        self.assertItemsEqual(xpath.resolve('child::segid', self.graph).nodes.keys(), [2, 20])
        self.assertItemsEqual(xpath.resolve('//residue[3]/following-sibling::residue', self.graph).nodes.keys(), [21])
        self.assertItemsEqual(xpath.resolve('//atom/ancestor::segid', self.graph).nodes.keys(), [2, 20])
        self.assertItemsEqual(xpath.resolve('//residue/parent::*', self.graph).nodes.keys(), [2, 20])

    def test_query_different_sepchar(self):
        """
        Test XpathExpressionEvaluator use with different sep char (.)
        """

        xpath = XpathExpressionEvaluator(sep='.')

        xpath.resolve('system.segid.residue', self.graph)
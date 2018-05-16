# -*- coding: utf-8 -*-

"""
file: module_validators_test.py

Unit tests for custom Haddock parameter validators
"""

import os
import unittest2
import pkg_resources

from lie_graph import GraphAxis
from lie_graph.graph_io.io_web_format import read_web
from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools

from lie_haddock.haddock_model_classes import haddock_orm
from lie_haddock.haddock_io.haddock_io_tbl import validate_tbl
from lie_haddock.haddock_io.haddock_io_pdb import PDBParser

currpath = os.path.dirname(__file__)
schemadir = pkg_resources.resource_filename('lie_haddock', '/schemas/endpoints')


class TestHaddockDataModelTBLValidation(unittest2.TestCase):

    webfile = os.path.join(currpath, '../', 'files', 'haddock_params_complete.web')

    def setUp(self):
        """
        Haddock test class setup

        Load a .web file for each test
        """

        self.web = GraphAxis()
        self.web.node_tools = NodeAxisTools
        self.web = read_web(self.webfile, graph=self.web)
        self.web.orm = haddock_orm

    def test_validation_function(self):
        """
        Test plain use of validate_tbl function for non PCS data
        """

        for data in ('tbldata', 'dihedraldata', 'rdcdata', 'danidata'):
            v = self.web.query_nodes(key=data)

            if not v.empty():
                self.assertTrue(validate_tbl(v.value, pcs=False))

    def test_validation_function_pcs(self):
        """
        Test plain use of validate_tbl function for PCS data
        """

        for data in ('tensordata', 'pcsdata'):
            v = self.web.query_nodes(key=data)

            if not v.empty():
                self.assertTrue(validate_tbl(v.value, pcs=True))

    def test_validation_class(self):
        """
        Test validate_tbl as part of data model ORM class
        """

        for data in ('tbldata', 'dihedraldata', 'rdcdata', 'danidata', 'tensordata', 'pcsdata'):
            v = self.web.query_nodes(key=data)

            if not v.empty():
                self.assertTrue(v.validate())


class TestHaddockDataModelPDBValidation(unittest2.TestCase):

    pdbfile = os.path.join(currpath, '../', 'files', 'protein1.pdb')

    def test_parse_pdb(self):
        """
        Test default parsing of PDB to Pandas DataFrame
        """

        pdbfile = open(self.pdbfile, 'r').read()

        parser = PDBParser()
        pdbdf = parser.parse_to_pandas(pdbfile)

        self.assertItemsEqual(pdbdf['chain'].unique(), [None])
        self.assertItemsEqual(pdbdf['segid'].unique(), ['A'])
        self.assertItemsEqual(pdbdf['resnum'].unique(), range(89, 137))
        self.assertItemsEqual(pdbdf['resname'].unique(), ['ARG', 'ALA', 'GLN', 'PRO', 'LYS', 'TYR', 'SER', 'VAL',
                                                          'ASP', 'GLU', 'ASN', 'GLY', 'THR', 'TRP', 'ILE', 'MET',
                                                          'LEU', 'PHE'])



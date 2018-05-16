# -*- coding: utf-8 -*-

"""
file: module_datamodel_test.py

Unit tests for the Haddock graph based data model and helper functions
"""

import os
import json
import jsonschema
import unittest2
import pkg_resources

from lie_graph import GraphAxis
from lie_graph.graph_io.io_web_format import read_web
from lie_graph.graph_io.io_dict_format import write_dict
from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools

from lie_haddock.haddock_model_classes import haddock_orm
from lie_haddock.haddock_model import (remove_haddock_data_block, load_project, save_project, edit_parameter_block,
                                           new_haddock_data_block_from_template, new_parameter_block)

currpath = os.path.dirname(__file__)
schemadir = pkg_resources.resource_filename('lie_haddock', '/schemas/endpoints')


def schema_to_data(schema, defdict=None):

    default_data = defdict or {}

    properties = schema.get('properties', {})
    for key, value in properties.items():
        if 'properties' in value:
            default_data[key] = schema_to_data(value)
        else:
            default_data[key] = value.get('default')

    return default_data


@unittest2.skipIf(not os.path.exists(schemadir), "lie_haddock package not installed")
class TestHaddockDataModelBlockAdd(unittest2.TestCase):

    webfile = os.path.join(currpath, '../', 'files', 'haddock_params_base.web')

    def setUp(self):
        """
        Haddock test class setup

        Load a .web file for each test
        """

        self.web = GraphAxis()
        self.web.node_tools = NodeAxisTools
        self.web = read_web(self.webfile, graph=self.web)
        self.web.orm = haddock_orm

    def test_data_block_new(self):
        """
        Test creation of new Haddock parameter data block based on template
        """

        # Parse template
        template = os.path.join(schemadir, 'haddock-project-request.v1.json')
        parsed = schema_to_data(json.load(open(template)))

        # Data model from template and compare
        new = new_haddock_data_block_from_template(template)
        self.assertDictEqual(parsed['project'], write_dict(new.query_nodes(key='project')))

    def test_data_block_new_notemplate(self):
        """
        JSON Schema data file not available
        """

        self.assertRaises(IOError, new_haddock_data_block_from_template, '/file/not/exist.json')

    def test_data_block_new_append(self):
        """
        Test creation of new Haddock parameter data block and append to project
        """

        block_id, project = new_parameter_block(self.web, 'haddock-dani-request.v1', 'DANIParameters', max_mult=5)

        self.assertEqual(block_id, 'project.dan1')
        self.assertTrue('dan1' in self.web.keys())

    def test_data_block_new_append_maxmult(self):
        """
        Test max multiplication number of same block when adding new ones
        """

        for n in range(6):
            new_parameter_block(self.web, 'haddock-dani-request.v1', 'DANIParameters', max_mult=5)

        dan = self.web.query_nodes(haddock_type='DANIParameters')
        self.assertEqual(len(dan), 5)
        self.assertItemsEqual(dan.keys(), ['dan1', 'dan2', 'dan3', 'dan4', 'dan5'])

    def test_data_block_new_append_wrong_type(self):
        """
        Test creation of new Haddock parameter block but using wrong Haddock type
        """

        block_id, project = new_parameter_block(self.web, 'haddock-dani-request.v1', 'LOLParameters', max_mult=5)

        self.assertIsNone(block_id)
        self.assertTrue(self.web.query_nodes(key='LOLParameters').empty())
        self.assertTrue(self.web.query_nodes(key='DANIParameters').empty())


class TestHaddockDataModelBlockEdit(unittest2.TestCase):

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

    def test_data_block_edit_single(self):
        """
        Test edit of single parameter
        """

        params = edit_parameter_block(self.web, 'dan1', {'anis': 2.445})

        for model in (self.web, params):
            dan = model.query_nodes(key='dan1')
            self.assertEqual(dan.anis.value, 2.445)

    def test_data_block_edit_multiple(self):
        """
        Test edit of multiple nested parameter
        """

        to_edit = {'r': {'auto_passive': True}, 'moleculetype': 'DNA', 'fullyflex': {'segments': [1, 2, 3]}}
        params = edit_parameter_block(self.web, 'p1', to_edit)

        params = write_dict(params)
        params['project_id'] = 'testid'
        jschema = json.load(open(os.path.join(schemadir, 'haddock-partner-request.v1.json')))
        self.assertIsNone(jsonschema.validate(params, jschema))


class TestHaddockDataModelHelpers(unittest2.TestCase):

    webfile = os.path.join(currpath, '../', 'files', 'haddock_params_complete.web')
    tempfiles = []

    def setUp(self):
        """
        Haddock test class setup

        Load a .web file for each test
        """

        self.web = GraphAxis()
        self.web.node_tools = NodeAxisTools
        self.web = read_web(self.webfile, graph=self.web)
        self.web.orm = haddock_orm

    def tearDown(self):
        """
        tearDown method called after each unittest to cleanup
        the files directory
        """

        for tmp in self.tempfiles:
            if os.path.exists(tmp):
                os.remove(tmp)

    def test_project_load(self):
        """
        Test loading a Haddock project
        """

        project = load_project(self.webfile)
        self.assertTrue(project == self.web)

    def test_project_save(self):
        """
        Test export of project to Haddock .web format and save to file
        """

        # Export to file
        file_path = os.path.join(currpath, '../', 'files', 'export_test.web')
        self.tempfiles.append(file_path)

        save_project(self.web, file_path)
        self.assertTrue(os.path.isfile(file_path))

        # Import again and compare
        project = load_project(file_path)
        self.assertTrue(project == self.web)

    def test_data_block_remove(self):
        """
        Test removal of parameter data blocks from a project data model using
        the remove_haddock_data_block method
        """

        # Remove single parameter
        self.assertTrue(remove_haddock_data_block(self.web, 'auto_passive_radius'))
        self.assertTrue(self.web.query_nodes(key='auto_passive_radius').empty())

        # Remove 'mrswi' data block. Block should be gone, children also
        self.assertTrue(remove_haddock_data_block(self.web, 'mrswi'))
        self.assertTrue(self.web.query_nodes(key='mrswi').empty())
        self.assertTrue('mrswi' not in [n.parent().key for n in self.web.query_nodes(key='hot')])

        # Block does not exist
        root = self.web.getnodes(self.web.root)
        self.assertRaises(AttributeError, root.__getattr__, 'notpresent')
        self.assertFalse(remove_haddock_data_block(self.web, 'notpresent'))

        # Remove multiple
        self.assertFalse(remove_haddock_data_block(self.web, 'r'))
        self.assertTrue(remove_haddock_data_block(self.web, 'r', multiple=True))
        self.assertTrue(self.web.query_nodes(key='r').empty())

        # Remove nested parameters
        self.assertTrue(remove_haddock_data_block(self.web, 'p1.semiflex'))
        self.assertTrue('p1' in self.web.keys())
        self.assertFalse('semiflex' in root.p1.keys())

        # Nested block does not exist
        self.assertFalse(remove_haddock_data_block(self.web, 'p1.semiflex'))

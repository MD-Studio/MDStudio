# -*- coding: utf-8 -*-

"""
file: module_project_test.py

Unit tests for building a new Haddock project using the data model
"""

import os
import json
import jsonschema
import unittest2
import pkg_resources

from lie_graph.graph_io.io_web_format import read_web, write_web
from lie_graph.graph_io.io_dict_format import write_dict

from lie_haddock.haddock_model import (remove_haddock_data_block, load_project, save_project, edit_parameter_block,
                                       new_parameter_block, new_project)

currpath = os.path.dirname(__file__)
schemadir = pkg_resources.resource_filename('lie_haddock', '/schemas/endpoints')


def json_schema_validation(data, schema):
    """
    Validate added Haddock data model block against JSON schema
    :param data:    data block to validate
    :type data:     :py:dict
    :param schema:  JSON schema to validate against
    :type schema:   :py:str

    :return:        validation was successfull
    :rtype:         :py:bool
    """

    schema_file = open(os.path.join(schemadir, schema))
    js = json.load(schema_file)
    jsonschema.validate(data, js)
    try:
        jsonschema.validate(data, js)
    except:
        return False

    return True


class TestHaddockProjectBuild(unittest2.TestCase):

    files = os.path.join(currpath, '../', 'files')

    @classmethod
    def setUpClass(cls):
        """
        Start with creation of empty base project. All other test fixtures will
        operate on this project.
        """

        cls.project = new_project('test')

    @classmethod
    def tearDownClass(cls):
        """
        When we are done, test export of the project
        """

        runname = cls.project.query_nodes(key='runname')
        output_web_file = os.path.join(cls.files, '{0}.web'.format(runname.value))
        with open(output_web_file, 'w') as wf:
            wf.write(write_web(cls.project))

    def test_edit_base_project(self):
        """
        Test edit parameters on base project
        """

        projectdata = {'runname': 'test_project', 'structures_0': 100, 'structures_1': 50, 'waterrefine': 50,
                       'username': 'marcvdijk'}

        params = edit_parameter_block(self.project, 'project', projectdata)

        # Validate against JSON schema
        self.assertTrue(json_schema_validation({'project_id': 'test', 'project': write_dict(params, allow_none=False)},
                                               'haddock-project-request.v1.json'))

    def test_edit_first_partner(self):
        """
        Test adding of partner molecule
        """

        pdb = os.path.join(self.files, 'protein1.pdb')
        partnerdata = {
            'r': {'activereslist': [97, 98, 99, 100, 103, 104, 105, 106, 107],
                  'auto_passive': True},
            'pdbdata': open(pdb, 'r').read()
        }

        block_id, params = new_parameter_block(self.project, 'haddock-partner-request.v1',
                                               'HaddockPartnerParameters', max_mult=5)
        params = edit_parameter_block(self.project, block_id, partnerdata)
        valdict = {'project_id': 'test'}
        valdict.update(write_dict(params))

        self.assertIn(block_id, ('project.p1', 'project.p2'))
        self.assertTrue(json_schema_validation(valdict, 'haddock-partner-request.v1.json'))

    def test_edit_second_partner(self):
        """
        Test adding of partner molecule, a DNA molecule
        """

        pdb = os.path.join(self.files, 'protein2.pdb')
        partnerdata = {
            'activereslist': [8, 9, 10, 11, 28, 29, 30, 31],
            'auto_passive': False,
            'pdbdata': open(pdb, 'r').read(),
            'moleculetype': 'DNA'
        }

        block_id, params = new_parameter_block(self.project, 'haddock-partner-request.v1',
                                               'HaddockPartnerParameters', max_mult=5)
        params = edit_parameter_block(self.project, block_id, partnerdata)
        valdict = {'project_id': 'test'}
        valdict.update(write_dict(params))

        self.assertIn(block_id, ('project.p1', 'project.p2'))
        self.assertTrue(json_schema_validation(valdict, 'haddock-partner-request.v1.json'))

    def test_edit_flexranges(self):
        """
        Test adding of (semi)-flexible ranges to partner molecules
        """

        semiflex = [{'start': 96, 'end': 100}, {'start': 103, 'end': 107}]
        for i, range in enumerate(semiflex, start=1):
            block_id, params = new_parameter_block(self.project, 'haddock-flexrange-request.v1',
                                                   'Range', attach='p1.semiflex.segments')
            params = edit_parameter_block(self.project, block_id, range)
            valdict = {'project_id': 'test', 'item': write_dict(params)}

            self.assertEqual(block_id, 'project.p1.semiflex.segments.item{0}'.format(i))
            self.assertTrue(json_schema_validation(valdict, 'haddock-flexrange-request.v1.json'))

        # Validate SemiflexSegmentList separately
        sf = self.project.xpath('project.p1.semiflex', sep='.')
        self.assertTrue(sf.validate())

        fullyflex = {'start': 89, 'end': 95}
        block_id, params = new_parameter_block(self.project, 'haddock-flexrange-request.v1',
                                               'Range', attach='p1.fullyflex.segments')
        params = edit_parameter_block(self.project, block_id, fullyflex)
        valdict = {'project_id': 'test', 'item': write_dict(params)}

        # Validate SemiflexSegmentList separately
        sf = self.project.xpath('project.p1.fullyflex', sep='.')
        self.assertTrue(sf.validate())

        self.assertEqual(block_id, 'project.p1.fullyflex.segments.item1')
        self.assertTrue(json_schema_validation(valdict, 'haddock-flexrange-request.v1.json'))

    def test_edit_rdc_restraints(self):
        """
        Test adding RDC restraint data to the project
        """

        rdc = os.path.join(self.files, 'rdcdata.tbl')
        rdcdata = {
            'choice': 'XRDC',
            'rdcdata': open(rdc, 'r').read(),
            'constants': {'firstit': 0, 'lastit': 1}
        }

        block_id, params = new_parameter_block(self.project, 'haddock-rdc-request.v1',
                                               'RDCParameters', max_mult=5)
        params = edit_parameter_block(self.project, block_id, rdcdata)
        valdict = {'project_id': 'test'}
        valdict.update(write_dict(params))

        self.assertEqual(block_id, 'project.rdc1')
        self.assertTrue(json_schema_validation(valdict, 'haddock-rdc-request.v1.json'))

    def test_edit_pcs_restriants(self):
        """
        Test adding PCS restraint data to the project
        """

        pcs = os.path.join(self.files, 'tensordata.tbl')
        pcsdata = {'pcsdata': open(pcs, 'r').read()}

        valdict = {'project_id': 'test'}
        if 'tensordata' in pcsdata:
            params = edit_parameter_block(self.project, 'project.tensorfile', pcsdata)
            valdict.update(write_dict(params))

        block_id, params = new_parameter_block(self.project, 'haddock-pcs-request.v1',
                                               'PCSParameters', max_mult=10)
        params = edit_parameter_block(self.project, block_id, pcsdata)
        valdict.update(write_dict(params))

        self.assertEqual(block_id, 'project.pcs1')
        self.assertTrue(json_schema_validation(valdict, 'haddock-pcs-request.v1.json'))


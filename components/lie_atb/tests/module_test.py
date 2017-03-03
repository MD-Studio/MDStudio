# -*- coding: utf-8 -*-

"""
file: module_atb_test.py

Unit tests for the Automated Topology Builder server API
"""

import os
import sys
import json
import re
import unittest2

import urllib2

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

from   lie_atb          import ATBServerApi
from   lie_atb.settings import SETTINGS

class TestAPI(unittest2.TestCase):
    
    _files_dir = os.path.join(currpath, 'files')
    
    def setUp(self):
        """
        ConfigHandlerTests class setup
        
        Init Automated Topology Builder server API
        """
        
        self.api = ATBServerApi(api_token=SETTINGS['atb_api_token'],
                                timeout=SETTINGS['atb_api_timeout'],
                                debug=SETTINGS['atb_api_debug'],
                                host=SETTINGS['atb_url'])
        self.files_to_delete = []
    
    # def tearDown(self):
    #     """
    #     Cleanup after each unit test
    #     """
    #
    #     for dfile in self.files_to_delete:
    #         if os.path.isfile(dfile):
    #             os.remove(dfile)
    #
    # def test_molecule_query_iupac_name(self):
    #     """
    #     Test query for molecules using a the iupac name
    #     """
    #
    #     for iupac in ('ethanol','pyrene'):
    #         molecules = self.api.Molecules.search(iupac=iupac)
    #         self.assertTrue(len(molecules) > 0)
    #         self.assertTrue(all([m.iupac.lower() == iupac for m in molecules]))
    #
    # def test_molecule_query_common_name(self):
    #     """
    #     Test query for molecules using molecule common name
    #     """
    #
    #     for common_name in ('ethyloxidanyl', 'cyclohexane'):
    #         molecules = self.api.Molecules.search(common_name=common_name)
    #         self.assertTrue(len(molecules) > 0)
    #         self.assertTrue(all([m.common_name.lower() == common_name for m in molecules]))
    #
    # def test_molecule_query_formula(self):
    #     """
    #     Test query for molecules using molecular formula
    #     """
    #
    #     molecules = self.api.Molecules.search(formula='C2H6O')
    #     self.assertTrue(len(molecules) > 0)
    #     self.assertTrue(all([m.formula == 'C2H6O' for m in molecules]))
    #
    # def test_molecule_query_inchi(self):
    #     """
    #     Test query for molecules using InChi codes
    #
    #     Inchi query should have the format 'InChi=<inchi string>' where the
    #     forward slashes are replaced by '%2F', done by API
    #     """
    #
    #     inchi = 'InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3'
    #
    #     molecules = self.api.Molecules.search(InChI=inchi)
    #     self.assertTrue(len(molecules) > 0)
    #     self.assertTrue(all([m.inchi == inchi for m in molecules]))
    #
    # def test_molecule_query_nonexisting_key(self):
    #     """
    #     Test query using a key that does not exist in a molecular record or is
    #     not supported. These queries should result in the exception:
    #     urllib2.HTTPError: HTTP Error 404: Not Found
    #     """
    #
    #     self.assertRaises(urllib2.HTTPError, self.api.Molecules.search, molid=213367)
    #     self.assertRaises(urllib2.HTTPError, self.api.Molecules.search, notexist='not')
    #     self.assertRaises(urllib2.HTTPError, self.api.Molecules.search, netcharge=0)
    #
    # def test_molecule_query_getbymolid(self):
    #     """
    #     Test retrieval of molecule ID by ATB mol ID
    #     """
    #
    #     molecules = self.api.Molecules.molid(molid=36825)
    #     self.assertEqual(molecules.common_name, 'Pyrene')
    #
    # def test_molecule_query_bystructure(self):
    #     """
    #     Test structure based molecular query
    #
    #     Query supports structure files in PDF, SDF, MOL, MOL2 and INCHI formats
    #     Query includes netcharge as either undefined (*) or from +5 to -5
    #     """
    #
    #     query_file = os.path.join(self._files_dir, '36825_querystructure.pdb')
    #
    #     result = None
    #     with open(query_file) as pdb:
    #         result = self.api.Molecules.structure_search(structure_format='pdb', structure=pdb.read(), netcharge='*')
    #
    #     if result and type(result) == dict:
    #         print(result['status'])
    #
    # def test_host_url_reachable(self):
    #     """
    #     Test if the ATB server is reachable
    #     """
    #
    #     api = ATBServerApi(api_token=SETTINGS['atb_api_token'],
    #                        host='http://host.not.exist')
    #
    #     valid_atb_url = True
    #     try:
    #         response = api.Molecules.search(any='ethanol')
    #     except urllib2.URLError:
    #         valid_atb_url = False
    #         print('ATB server URL {0} not known/reachable'.format('http://host.not.exist'))
    #     except urllib2.HTTPError:
    #         valid_atb_url = False
    #         print('ATB query not valid or no valid token')
    #
    #     self.assertFalse(valid_atb_url)
    #
    # def test_host_token_not_valid(self):
    #     """
    #     Test server response if ATB token is not valid
    #     """
    #
    #     api = ATBServerApi(api_token='not valid token',
    #                        host=SETTINGS['atb_url'])
    #
    #     valid_atb_token = ''
    #     try:
    #         response = api.Molecules.search(any='ethanol')
    #     except urllib2.URLError, e:
    #         valid_atb_token = json.load(e)['error_msg']
    #     except urllib2.HTTPError, e:
    #         valid_atb_token = json.load(e)['error_msg']
    #
    #     self.assertEqual(valid_atb_token, u'Could not authenticate account')
    #
    # def test_molecules_structure_save(self):
    #     """
    #     Test saving queried molecules to file
    #     """
    #
    #     molecules = self.api.Molecules.search(any='ethanol')
    #     for fformat in ('pdb_aa', 'pdb_ua', 'pdb_allatom_unoptimised'):
    #         for molecule in molecules:
    #             pdb_path = os.path.join(self._files_dir, '{0}_{1}.{2}'.format(molecule.molid, fformat, fformat.split('_')[0]))
    #             self.files_to_delete.append(pdb_path)
    #
    #             mol = molecule.download_file(atb_format=fformat)
    #             with open(pdb_path, 'w') as outf:
    #                 outf.write(mol)
    #
    #     self.assertTrue(all([os.path.isfile(f) for f in self.files_to_delete]))
    #
    # def test_molecules_topoloy_lammps_save(self):
    #     """
    #     Test retrieval of files in LAMMPS format.
    #     """
    #
    #     molecule = self.api.Molecules.molid(molid=36825)
    #     for ffVersion in ('53A6', '54A7'):
    #         for fformat in ('lammps_allatom_optimised.lt', 'lammps_allatom_unoptimised.lt', 'lammps_uniatom_optimised.lt', 'lammps_uniatom_unoptimised.lt'):
    #             pdb_path = os.path.join(self._files_dir, '{0}_{1}_{2}.{3}'.format(molecule.molid, fformat.split('.')[0], ffVersion, fformat.split('.')[1]))
    #             self.files_to_delete.append(pdb_path)
    #
    #             mol = molecule.download_file(file=fformat, outputType='top', ffVersion=ffVersion, hash='HEAD')
    #             with open(pdb_path, 'w') as outf:
    #                 outf.write(mol)
    #
    #     self.assertTrue(all([os.path.isfile(f) for f in self.files_to_delete]))
    #
    # def test_molecules_topoloy_gromos96_save(self):
    #     """
    #     Test retrieval of files in GROMOS96 format.
    #     """
    #
    #     molecule = self.api.Molecules.molid(molid=36825)
    #     for ffVersion in ('53A6', '54A7'):
    #         for fformat in ('mtb96_allatom', 'mtb96_uniatom'):
    #             pdb_path = os.path.join(self._files_dir, '{0}_{1}_{2}.{3}'.format(molecule.molid, fformat, ffVersion, fformat.split('_')[1]))
    #             self.files_to_delete.append(pdb_path)
    #
    #             mol = molecule.download_file(file=fformat, outputType='top', ffVersion=ffVersion, hash='HEAD')
    #             with open(pdb_path, 'w') as outf:
    #                 outf.write(mol)
    #
    #     self.assertTrue(all([os.path.isfile(f) for f in self.files_to_delete]))
    #
    # def test_molecules_topoloy_gromos11_save(self):
    #     """
    #     Test retrieval of files in GROMOS11 format.
    #     """
    #
    #     molecule = self.api.Molecules.molid(molid=36825)
    #     for ffVersion in ('53A6', '54A7'):
    #         for fformat in ('mtb_allatom', 'mtb_uniatom'):
    #             pdb_path = os.path.join(self._files_dir, '{0}_{1}_{2}.{3}'.format(molecule.molid, fformat, ffVersion, fformat.split('_')[1]))
    #             self.files_to_delete.append(pdb_path)
    #
    #             mol = molecule.download_file(file=fformat, outputType='top', ffVersion=ffVersion, hash='HEAD')
    #             with open(pdb_path, 'w') as outf:
    #                 outf.write(mol)
    #
    #     self.assertTrue(all([os.path.isfile(f) for f in self.files_to_delete]))
    #
    # def test_molecules_structure_gromacs_save(self):
    #     """
    #     Test retrieval of structure files in GROMACS format
    #     """
    #
    #     molecule = self.api.Molecules.molid(molid=36825)
    #     for ffVersion in ('53A6', '54A7'):
    #         for fformat in ('rtp_allatom', 'rtp_uniatom'):
    #             pdb_path = os.path.join(self._files_dir, '{0}_{1}_{2}.itp'.format(molecule.molid, fformat, ffVersion))
    #             self.files_to_delete.append(pdb_path)
    #
    #             mol = molecule.download_file(file=fformat, outputType='top', ffVersion=ffVersion, hash='HEAD')
    #             with open(pdb_path, 'w') as outf:
    #                 outf.write(mol)
    #
    #     self.assertTrue(all([os.path.isfile(f) for f in self.files_to_delete]))
    #
    # def test_molecules_structure_pdb_save(self):
    #     """
    #     Test retrieval of structure files in PDB format
    #     """
    #
    #     molecule = self.api.Molecules.molid(molid=36825)
    #     for ffVersion in ('53A6', '54A7'):
    #         for fformat in ('pdb_allatom_optimised', 'pdb_allatom_unoptimised', 'pdb_uniatom_optimised', 'pdb_uniatom_unoptimised'):
    #             pdb_path = os.path.join(self._files_dir, '{0}_{1}_{2}.pdb'.format(molecule.molid, fformat, ffVersion))
    #             self.files_to_delete.append(pdb_path)
    #
    #             mol = molecule.download_file(file=fformat, outputType='top', ffVersion=ffVersion, hash='HEAD')
    #             with open(pdb_path, 'w') as outf:
    #                 outf.write(mol)
    #
    #     self.assertTrue(all([os.path.isfile(f) for f in self.files_to_delete]))
    #
    # def test_molecules_structure_apbs_save(self):
    #     """
    #     Test retrieval of structure files in APBS format
    #     """
    #
    #     molecule = self.api.Molecules.molid(molid=36825)
    #     for ffVersion in ('53A6', '54A7'):
    #         for fformat in ('pqr_allatom_optimised', 'pqr_allatom_unoptimised', 'pqr_uniatom_optimised', 'pqr_uniatom_unoptimised'):
    #             pdb_path = os.path.join(self._files_dir, '{0}_{1}_{2}.pqr'.format(molecule.molid, fformat, ffVersion))
    #             self.files_to_delete.append(pdb_path)
    #
    #             mol = molecule.download_file(file=fformat, outputType='cry', ffVersion=ffVersion, hash='HEAD')
    #             with open(pdb_path, 'w') as outf:
    #                 outf.write(mol)
    #
    #     self.assertTrue(all([os.path.isfile(f) for f in self.files_to_delete]))
    #
    # def test_molecules_structure_cns_save(self):
    #     """
    #     Test retrieval of structure files in CNS format
    #     """
    #
    #     molecule = self.api.Molecules.molid(molid=36825)
    #     for ffVersion in ('53A6', '54A7'):
    #         for fformat in ('cns_allatom_top', 'cns_allatom_param', 'cns_uniatom_top', 'cns_uniatom_param'):
    #             pdb_path = os.path.join(self._files_dir, '{0}_{1}_{2}.cns'.format(molecule.molid, fformat, ffVersion))
    #             self.files_to_delete.append(pdb_path)
    #
    #             mol = molecule.download_file(file=fformat, outputType='cry', ffVersion=ffVersion, hash='HEAD')
    #             with open(pdb_path, 'w') as outf:
    #                 outf.write(mol)
    #
    #     self.assertTrue(all([os.path.isfile(f) for f in self.files_to_delete]))
    #
    # def test_molecules_structure_cif_save(self):
    #     """
    #     Test retrieval of structure files in CIF format
    #     """
    #
    #     molecule = self.api.Molecules.molid(molid=36825)
    #     for ffVersion in ('53A6', '54A7'):
    #         for fformat in ('cif_allatom', 'cif_allatom_extended', 'cif_uniatom', 'cif_uniatom_extended'):
    #             pdb_path = os.path.join(self._files_dir, '{0}_{1}_{2}.cif'.format(molecule.molid, fformat, ffVersion))
    #             self.files_to_delete.append(pdb_path)
    #
    #             mol = molecule.download_file(file=fformat, outputType='cry', ffVersion=ffVersion, hash='HEAD')
    #             with open(pdb_path, 'w') as outf:
    #                 outf.write(mol)
    #
    #     self.assertTrue(all([os.path.isfile(f) for f in self.files_to_delete]))

    def test_submit_job_allreadycalculated(self):
        """
        Test submitting a job that has already been calculated once.
        Should fail
        """

        # molecule = self.api.Molecules.molid(molid=21)
        # mol = molecule.download_file(file='pdb_allatom_optimised', outputType='top', ffVersion='54A7', hash='HEAD')
        mol = open('/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/tmp/cid005.pdb', 'r').read()
        try:
            response = self.api.Molecules.submit(pdb=mol, netcharge=0, moltype='heteromolecule', public=True)
        except urllib2.HTTPError, error:
            response = json.load(error)
                
        if response.get(u'status', None) == u'error':
            if response.get(u'error_msg','').startswith('Your submission matched a previously'):
                m = re.search('(?<=molid=)[0-9]*', response.get(u'error_msg',''))
                if m:
                    molid = m.group()
                    if molid.isdigit():
                        molid = int(molid)
                        print(molid)
                    
                    
    # def test_rmsd_methods(self):
    #     """
    #     Test RMSD matching methods
    #     """
    #
    #     ethanol_molids = [15608, 23009, 26394]
    #
    #     result1 = self.api.RMSD.matrix(molids=ethanol_molids)
    #     result2 = self.api.RMSD.align(molids=ethanol_molids[0:2])
    #     result3 = self.api.RMSD.align(
    #         reference_pdb=self.api.Molecules.download_file(atb_format=u'pdb_aa', molid=ethanol_molids[0]),
    #         pdb_0=self.api.Molecules.download_file(atb_format=u'pdb_aa', molid=ethanol_molids[1]),
    #     )
    #
    #     self.assertEqual(result2['rmsd'], result3['rmsd'])
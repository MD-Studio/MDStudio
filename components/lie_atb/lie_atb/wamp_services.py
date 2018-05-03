# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import json
import re

from lie_atb import ATBServerApi, ATB_Mol
from lie_atb.settings import *
from mdstudio.api.endpoint import endpoint
from mdstudio.component.session import ComponentSession

if sys.version_info.major == 3:
    from urllib.error import HTTPError, URLError
else:
    from urllib2 import HTTPError, URLError


class ATBWampApi(ComponentSession):
    """
    Automated Topology Builder API WAMP methods.
    """

    def authorize_request(self, uri, claims):
        return True

    def _parse_server_error(self, error):
        """
        Parse ATB server JSON error construct
        """

        error_dict = {}
        if hasattr(error, 'read'):
            try:
                error_dict = json.load(error)
                self.log.error('ATB server error: {0}'.format(error_dict.get('error_msg')))
            except Exception:
                self.log.error('Unknown ATB server error')

        return error_dict

    def _exceute_api_call(self, call, **kwargs):
        """
        Execute ATB server API call
        """

        try:
            return call(**kwargs)
        except URLError as error:
            self.log.error('ATB server URL {0} not known/reachable'.format(SETTINGS['atb_url']))
            return self._parse_server_error(error)
        except HTTPError as error:
            return self._parse_server_error(error)

    def _init_atb_api(self, api_token=None):
        """
        Start ATB server API interface.

        The ATB API is initiated at every WAMP method request using a global
        or user specific ATB API token.

        :param api_token: valid ATB server API token
        :type api_token:  :py:str

        :rtype:           ATBServerApi object
        """

        if not api_token:
            self.log.error('Using the ATB server requires a valid API token')
            return None

        api = ATBServerApi(api_token=api_token,
                           timeout=SETTINGS['atb_api_timeout'],
                           debug=SETTINGS['atb_api_debug'],
                           host=SETTINGS['atb_url'])
        api.API_FORMAT = u'json'
        return api

    @endpoint('submit', 'atb_submit_request', 'atb_submit_response')
    def atb_submit_calculation(self, request, claims):
        """
        Submit a new calculation to the ATB server
        """

        # Init ATBServerApi
        api = self._init_atb_api(api_token=request['atb_api_token'])
        if not api:
            self.log.error('Unable to use the ATB API')

        # Open file if needed
        if request['isfile'] and os.path.isfile(request['pdb']):
            request['pdb'] = open(request['pdb'], 'r').read()

        response = self._exceute_api_call(api.Molecules.submit, pdb=request['pdb'], netcharge=request['netcharge'],
                                          moltype=request['moltype'], public=request['public'])
        if response and response.get(u'status', None) == u'error':

            # Check if molecule has been calculated already
            if response.get(u'error_msg', '').startswith('Your submission matched a previously'):
                # Extract molid from response
                m = re.search('(?<=molid=)[0-9]*', response.get(u'error_msg', ''))
                molid = None
                if m:
                    molid = m.group()
                    if molid.isdigit():
                        molid = int(molid)

                # Get the molecule data for molid
                response = [self._exceute_api_call(api.Molecules.molid, molid=molid)]
                return {'result': [mol.moldict for mol in response if isinstance(mol, ATB_Mol)]}

    @endpoint('get_structure', 'atb_get_structure_request', 'atb_get_structure_response')
    def atb_structure_download(self, request, claims):
        """
        Retrieve a structure file from the ATB server by molid

        Supports download of structures in the following file formats:
        - pqr_allatom_optimised:    APBS pqr format
        - pqr_allatom_unoptimised:  APBS pqr format
        - pqr_uniatom_optimised:    APBS pqr format
        - pqr_uniatom_unoptimised:  APBS pqr format
        - pdb_allatom_optimised:    PDB format
        - pdb_allatom_unoptimised:  PDB format
        - pdb_uniatom_optimised:    PDB format
        - pdb_uniatom_unoptimised:  PDB format
        - cif_allatom:              CIF format
        - cif_allatom_extended:     CIF format
        - cif_uniatom:              CIF format
        - cif_uniatom_extended:     CIF format
        """

        if request['fformat'] not in SUPPORTED_STRUCTURE_FILE_FORMATS:
            self.log.error('Structure format {0} not supported'.format(request['fformat']))
            return

        # Init ATBServerApi
        api = self._init_atb_api(api_token=request['atb_api_token'])
        if not api:
            self.log.error('Unable to use the ATB API')
            return

        # Get the molecule by molid
        molecule = self._exceute_api_call(api.Molecules.molid, molid=request['molid'])
        filename = None
        if 'workdir' in request:
            filename = os.path.join(request['workdir'], '{0}.{1}'.format(request['fformat'],
                                                            SUPPORTED_FILE_EXTENTIONS.get(request['fformat'], 'txt')))

        if molecule and isinstance(molecule, ATB_Mol):
            structure = self._exceute_api_call(molecule.download_file, file=request['fformat'],
                                               outputType=SUPPORTED_STRUCTURE_FILE_FORMATS.get(request['fformat'], 'cry'),
                                               ffVersion=request['ffversion'], hash=request['atb_hash'], fnme=filename)
            return structure
        else:
            self.log.error('Unable to retrieve structure file for molid: {0}'.format(request['molid']))

    @endpoint('get_topology', 'atb_get_topology_request', 'atb_get_topology_response')
    def atb_topology_download(self, request, claims):
        """
        Retrieve a topology and parameter files from the ATB server by molid

        Supports download of structures in the following file formats:
        - lammps_allatom_optimised:     LAMMPS MD
        - lammps_allatom_unoptimised:   LAMMPS MD
        - lammps_uniatom_optimised:     LAMMPS MD
        - lammps_uniatom_unoptimised:   LAMMPS MD
        - mtb96_allatom:                GROMOS96
        - mtb96_uniatom:                GROMOS96
        - mtb_allatom:                  GROMOS11
        - mtb_uniatom:                  GROMOS11
        - rtp_allatom:                  GROMACS
        - rtp_uniatom:                  GROMACS
        - cns_allatom_top:              CNS
        - cns_allatom_param:            CNS
        - cns_uniatom_top:              CNS
        - cns_uniatom_param:            CNS
        """

        if request['fformat'] not in SUPPORTED_TOPOLOGY_FILE_FORMATS:
            self.log.error('Structure format {0} not supported'.format(request['fformat']))
            return

        # Init ATBServerApi
        api = self._init_atb_api(api_token=request['atb_api_token'])
        if not api:
            self.log.error('Unable to use the ATB API')
            return

        # Get the molecule by molid
        molecule = self._exceute_api_call(api.Molecules.molid, molid=request['molid'])
        filename = None
        if 'workdir' in request:
            filename = os.path.join(request['workdir'], '{0}.{1}'.format(request['fformat'],
                                                            SUPPORTED_FILE_EXTENTIONS.get(request['fformat'], 'top')))

        if molecule and isinstance(molecule, ATB_Mol):
            structure = self._exceute_api_call(molecule.download_file,
                                               file=SUPPORTED_TOPOLOGY_FILE_FORMATS[request['fformat']],
                                               outputType='top', ffVersion=request['ffversion'],
                                               hash=request['atb_hash'], fnme=filename)
            return structure
        else:
            self.log.error('Unable to retrieve topology/prameter file for molid: {0}'.format(request['molid']))

    @endpoint('structure_query', 'atb_structure_query_request', 'atb_structure_query_response')
    def atb_structure_query(self, request, claims):
        """
        Query the ATB server database for molecules based on a structure

        16-11-2017: Method only works with HTTP GET
        """

        # Open file if needed
        if request['isfile'] and os.path.isfile(request['mol']):
            request['mol'] = open(request['mol'], 'r').read()

        # Init ATBServerApi
        api = self._init_atb_api(api_token=request['atb_api_token'])
        if not api:
            self.log.error('Unable to use the ATB API')
            return

        result = self._exceute_api_call(api.Molecules.structure_search,
                                        structure_format=request['structure_format'],
                                        structure=request['mol'],
                                        netcharge=request.get('netcharge', '*'),
                                        method=u'GET')

        output = {'matches': result.get('matches', [])}
        if 'search_molecule' in result:
            for key in ('inchi', 'inchi_key'):
                output['search_{0}'.format(key)] = result['search_molecule'][key]

        return output

    @endpoint('molecule_query', 'atb_molecule_query_request', 'atb_molecule_query_response')
    def atb_molecule_query(self, request, claims):
        """
        Query the ATB server database for molecules based on molecule meta-data

        The ATB server molecules database can be queried using the
        ./api/v0.1/molecules/search.py endpoint using any of the following query
        attributes or 'any' for a whildcard search. Multiple query attributes
        will be chained using the AND logical operator.

        iupac:              the official IUPAC name of the  molecule (str)
        inchi_key:          the unique InChI code of the molecule (str)
        smiles:             canonical SMILES of the molecule (str)
        common_name:        the common name of the molecule (str)
        formula:            the molecular formula (e.a. C2H6O) (str)
        maximum_qm_level:   string of comma seperated integers.
        curation_trust:     level of expected accuracy of the molecule parameters
                            as string of comma seperated integers. 0 by default:
                            -1 = unfinished ATB molecule
                             0 = finished ATB molecule
                             1 = manual parameters from reliable users
                             2 = manual parameters from official source
        is_finished:        are calculations for the molecule still running
        user_label:         any user specific label that may have been given to
                            the molecule.
        is_finished:        query for finished molecules only
        max_atoms:          maximum number of atoms (int)
        min_atoms:          minimum number of atoms (int)
        has_pdb_hetId:      molecule has PDB heteroatom ID (bool)
        match_partial:      enable partial matching of string attributes (bool)
                            False by default.

        Query values are case insensitive but the attributes (keys) are.
        """

        # Init ATBServerApi
        api = self._init_atb_api(api_token=request['atb_api_token'])
        if not api:
            self.log.error('Unable to use the ATB API')
            return

        # Get molecule directly using ATB molid
        if 'molid' in request:
            response = [self._exceute_api_call(api.Molecules.molid, molid=request['molid'])]
        else:
            # Execute ATB molecule search query
            response = self._exceute_api_call(api.Molecules.search, **request)

        if isinstance(response, list):
            if not len(response):
                self.log.info('ATB molecule query did not yield any results')
            return {'result': []}
        else:
            self.log.error('Unable to execute ATB molecule query')

# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import json
import jsonschema
import tempfile

from StringIO import StringIO
from Bio.PDB import PDBList
from Bio.PDB.PDBIO import PDBIO
from Bio.PDB.PDBParser import PDBParser

from lie_structures import settings, toolkits
from lie_structures.settings import _schema_to_data, STRUCTURES_SCHEMA, BIOPYTHON_SCHEMA
from lie_structures.cheminfo_wamp.cheminfo_descriptors_wamp import CheminfoDescriptorsWampApi
from lie_structures.cheminfo_wamp.cheminfo_molhandle_wamp import CheminfoMolhandleWampApi
from lie_structures.cheminfo_wamp.cheminfo_fingerprints_wamp import CheminfoFingerprintsWampApi
from mdstudio.api.endpoint import endpoint
from mdstudio.component.session import ComponentSession

STRUCTURES_SCHEMA = json.load(open(STRUCTURES_SCHEMA))
BIOPYTHON_SCHEMA = json.load(open(BIOPYTHON_SCHEMA))


class StructuresWampApi(
        ComponentSession, CheminfoDescriptorsWampApi, CheminfoMolhandleWampApi,
        CheminfoFingerprintsWampApi):
    """
    Structure database WAMP methods.
    """
    def authorize_request(self, uri, claims):
        return True

    @endpoint('supported_toolkits', 'supported_toolkits_request', 'supported_toolkits_response')
    def supported_toolkits(self, request, claims):
        """
        Query available toolkits.
        """
        return {'status': 'completed', 'toolkits': toolkits.keys()}

    @endpoint('remove_residues', 'remove_residues_request', 'remove_residues_response')
    def remove_residues(self, request, claims):
        """
        Remove residues from a PDB structure
        """
        # Parse the structure
        parser = PDBParser(PERMISSIVE=True)

        if kwargs.get('from_file', False):
            struc_obj = open(kwargs.get('mol'), 'r')
        else:
            struc_obj = StringIO(kwargs.get('mol'))

        structure = parser.get_structure('mol_object', struc_obj)
        struc_obj.close()

        to_remove = [r.upper() for r in kwargs.get('residues', [])]
        removed = []
        for model in structure:
            for chain in model:
                for residue in chain:
                    if residue.get_resname() in to_remove:
                        chain.detach_child(residue.id)
                        removed.append(residue.get_resname())
                if len(chain) == 0:
                    model.detach_child(chain.id)
        self.log.info('Removed residues: {0}'.format(','.join(removed)))

        # Save to file or string
        pdbio = PDBIO()
        pdbio.set_structure(structure)

        session['status'] = 'completed'
        if kwargs.get('workdir'):
            outfile = os.path.join(kwargs.get('workdir'), 'structure.pdb')
            pdbio.save(outfile)
            return {'session': session, 'mol': outfile}
        else:
            outfile = StringIO()
            pdbio.save(outfile)
            outfile.seek(0)
            return {'session': session, 'mol': outfile.read()}

    @endpoint('retrieve_rcsb_structure', 'retrieve_rcsb_structure_request', 'retrieve_rcsb_structure_response')
    def fetch_rcsb_structure(self, session=None, **kwargs):
        """
        Download a structure file from the RCSB database using a PDB ID
        """
        # Load configuration and update
        config = _schema_to_data(BIOPYTHON_SCHEMA)
        config.update(kwargs)

        # Validate the configuration
        try:
            jsonschema.validate(config, BIOPYTHON_SCHEMA)
        except ValueError, e:
            self.log.error('Unvalid function arguments: {0}'.format(e))
            session['status'] = 'failed'
            return {'session': session}

        # Create workdir and save file
        workdir = os.path.join(config.get('workdir', tempfile.gettempdir()))
        if not os.path.isdir(workdir):
            os.makedirs(workdir)

        # Retrieve the PDB file
        pdb_id = config['pdb_id'].upper()
        pdb = PDBList()
        dfile = pdb.retrieve_pdb_file(pdb_id,
                              file_format=config.get('rcsb_file_format', 'pdb'),
                              pdir=workdir,
                              overwrite=True)

        # Change file extension
        base, ext = os.path.splitext(dfile)
        if ext == '.ent':
            os.rename(dfile, '{0}.pdb'.format(base))
            dfile = '{0}.pdb'.format(base)

        # Return file path if workdir in function arguments else return
        # file content inline.
        if os.path.isfile(dfile):
            session['status'] = 'completed'
            if 'workdir' in config:
                return {'session': session, 'mol': dfile}
            else:
                return {'session': session, 'mol': open(dfile).read()}

        self.log.error('Unable to download structure: {0}'.format(pdb_id), **session)
        session['status'] = 'failed'
        return {'session': session}


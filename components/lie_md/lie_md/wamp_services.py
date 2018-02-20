# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""
from lie_md.cerise_interface import (
    call_cerise_gromit, create_cerise_config)
from lie_md.md_config import set_gromacs_input
from mdstudio.api.endpoint import endpoint
from mdstudio.component.session import ComponentSession
import json
import os


class MDWampApi(ComponentSession):
    """
    Molecular dynamics WAMP methods.
    """
    def authorize_request(self, uri, claims):
        return True

    @endpoint('liemd', 'liemd_request', 'liemd_response')
    def run_gromacs_liemd(self, request, claims):
        """
        First it calls gromit to compute the Ligand-solute energies, then
        calls gromit to calculate the protein-ligand energies.

        The Cerise-client infrastructure is used to perform the computations
        in a remote server, see:
        http://cerise-client.readthedocs.io/en/master/index.html

        This function expects the following keywords files to call gromit:
            * protein_top
            * ligand_file
            * topology_file
            * protein_file (optional)

        Further include files (e.g. *itp files) can be included as a list:
        include=[atom_types.itp, another_itp.itp]

        To perform the energy decomposition a list of the numerical residues
        identifiers is expected, for example:
        residues=[1, 5, 7, 8]

        Note: the protein_file arguments is optional if you do not provide it
        the method will perform a SOLVENT LIGAND MD if you provide the
        `protein_file` it will perform a PROTEIN-LIGAND MD.
        """
        with open("request.json", "w") as f:
            json.dump(request, f)

        task_id = self.component_config.session.session_id
        self.log.info("starting liemd task_id:{}".format(task_id))
        workdir = request.get('workdir', os.getcwd())

        # Load GROMACS configuration
        gromacs_config = set_gromacs_input(request, workdir)

        with open("gromacs.json", "w") as f:
            json.dump(gromacs_config, f)

        # # Cerise Configuration
        # cerise_config = create_cerise_config(
        #     request['path_cerise_config'], session, request['cwl_workflow'], request['protein_file'])

        # # Run the MD and retrieve the energies
        # output = call_cerise_gromit(
        #     gromacs_config, cerise_config, self.db['cerise'])

        # session['status'] = 'completed'

        # return {'session': session, 'output': output}

        return {"output": {"answer": 42}}

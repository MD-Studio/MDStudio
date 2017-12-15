# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import json
import shutil
import json
from pprint import pprint

from autobahn import wamp
from autobahn.wamp.types import RegisterOptions
from twisted.internet.defer import inlineCallbacks, returnValue

from mdstudio.api.endpoint import endpoint
from mdstudio.component.session import ComponentSession
from lie_md.gromacs_gromit import gromit_cmd
from lie_md.settings import SETTINGS, GROMACS_LIE_SCHEMA

gromacs_schema = json.load(open(GROMACS_LIE_SCHEMA))

class MDWampApi(ComponentSession):
    """
    MD WAMP methods.
    """

    def pre_init(self):
        self.component_config.static.vendor = 'mdgroup'
        self.component_config.static.component = 'md'

    def authorize_request(self, uri, claims):
        return True

    @wamp.register(u'mdgroup.md.endpoint.gromacs.liemd')
    def run_gromacs_liemd(
            self, session={}, protein_file=None, ligand_file=None,
            topology_file=None, **kwargs):

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load GROMACS configuration and update
        gromacs_config = self.package_config.dict()

        # Create workdir and save file
        workdir = os.path.join(kwargs.get('workdir', tempfile.gettempdir()))
        if not os.path.isdir(workdir):
            os.mkdir(workdir)
        os.chdir(workdir)

        # Store protein file if available
        if protein_file:
            protdsc = os.path.join(workdir, 'protein.pdb')
            with open(protdsc, 'w') as inp:
                inp.write(protein_file)

        # Store ligand file if available
        if ligand_file:
            ligdsc = os.path.join(workdir, 'ligand.pdb')
            try:
                if os.path.isfile(ligand_file):
                    shutil.copy(ligand_file, ligdsc)
            except:
                with open(ligdsc, 'w') as inp:
                    inp.write(ligand_file)

        # Save ligand topology files
        if topology_file:
            topdsc = os.path.join(workdir, 'ligtop.itp')
            try:
                if os.path.isfile(
                        os.path.join(topology_file, 'input_GMX.itp')):
                    shutil.copy(
                        os.path.join(topology_file, 'input_GMX.itp'), topdsc)
            except:        
                with open(topdsc, 'w') as inp:
                    inp.write(topology_file)

        # Copy script files to the working directory
        for script in ('getEnergies.py', 'gmx45md.sh'):
            src = os.path.join(__rootpath__, 'scripts/{0}'.format(script))
            dst = os.path.join(workdir, script)
            shutil.copy(src, dst)

        # Fix topology ligand
        itpOut = 'ligand.itp'
        results = correctItp(topdsc, itpOut, posre=True)

        # Prepaire simulation
        gromacs_config['charge'] = results['charge']
        gmxRun = gromit_cmd(gromacs_config)

        if protein_file:
            gmxRun += '-f {0} '.format(os.path.basename(protdsc))

        if ligand_file:
            gmxRun += '-l {0},{1} '.format(
                os.path.basename(ligdsc), os.path.basename(results['itp']))

        # Prepaire post analysis (energy extraction)
        GMXRC = 'mock_path_to_gmxrc'
        eneRun = 'python getEnergies.py -gmxrc {0} -ene -o ligand.ene'.format(GMXRC)

        # write executable
        with open('run_md.sh', 'w') as outFile:
            outFile.write("{0}\n".format(gmxRun))
            outFile.write("{0}\n".format(eneRun))

        session['status'] = 'completed'

        return {'session': session, 'output': 'nothing'}


def make(config):
    """
    Component factory

    This component factory creates instances of the application component
    to run.

    The function will get called either during development using an
    ApplicationRunner, or as a plugin hosted in a WAMPlet container such as
    a Crossbar.io worker.
    The LieApplicationSession class is initiated with an instance of the
    ComponentConfig class by default but any class specific keyword arguments
    can be consument as well to populate the class session_config and
    package_config dictionaries.

    :param config: Autobahn ComponentConfig object
    """

    if config:
        return MDWampApi(config, package_config=SETTINGS)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio Molecular Dynamics WAMPlet',
                'description': 'WAMPlet proving LIEStudio molecular dynamics endpoints'}

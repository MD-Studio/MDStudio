# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import json
import os
import shutil

from autobahn import wamp

from lie_system import LieApplicationSession, WAMPTaskMetaData
from lie_md import __rootpath__
from lie_md.gromacs_topology_amber import correctItp
from lie_md.gromacs_gromit import gromit_cmd
from lie_md.settings import SETTINGS, GROMACS_LIE_SCHEMA

gromacs_schema = json.load(open(GROMACS_LIE_SCHEMA))


class MDWampApi(LieApplicationSession):
    """
    Molecular dynamics WAMP methods.
    """

    require_config = ['system']

    @wamp.register(u'liestudio.gromacs.liemd')
    def run_gromacs_liemd(
            self, session={}, protein_file=None, ligand_file=None,
            topology_file=None, **kwargs):
        """
        Call gromacs using the Cerise-client infrastructure:
        http://cerise-client.readthedocs.io/en/master/index.html
        """
        workdir = kwargs['workdir']

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load GROMACS configuration and update
        gromacs_config = self.package_config.dict()

        # Store protein file if available
        store_structure_in_file(
            protein_file, workdir, 'protein')

        # Store ligand file if available
        store_structure_in_file(
            ligand_file, workdir, 'ligand')

        # Save ligand topology files
        store_structure_in_file(
            topology_file, workdir, 'ligtop', ext='itp')

        # # Copy script files to the working directory
        # for script in ('getEnergies.py', 'gmx45md.sh'):
        #     src = os.path.join(__rootpath__, 'scripts/{0}'.format(script))
        #     dst = os.path.join(workdir, script)
        #     shutil.copy(src, dst)

        # # Fix topology ligand
        # itpOut = 'ligand.itp'
        # results = correctItp(topdsc, itpOut, posre=True)

        # # Prepaire simulation
        # gromacs_config['charge'] = results['charge']
        # gmxRun = gromit_cmd(gromacs_config)

        # if protein_file:
        #     gmxRun += '-f {0} '.format(os.path.basename(protdsc))

        # if ligand_file:
        #     gmxRun += '-l {0},{1} '.format(
        #         os.path.basename(ligdsc), os.path.basename(results['itp']))

        # # Prepaire post analysis (energy extraction)
        # eneRun = 'python getEnergies.py -gmxrc {0} -ene -o ligand.ene'.format(GMXRC)

        # # write executable
        # with open('run_md.sh', 'w') as outFile:
        #     outFile.write("{0}\n".format(gmxRun))
        #     outFile.write("{0}\n".format(eneRun))

        session['status'] = 'completed'

        return {'session': session, 'output': 'nothing'}


def store_structure_in_file(mol, workdir, name, ext='pdb'):
    """
    Store a molecule in a file if possible.
    """
    dest = os.path.join(workdir, '{}.{}'.format(name, ext))

    if mol is None:
        raise RuntimeError(
            "There is not {} available".format(name))

    elif os.path.isfile(mol):
        shutil.copy(mol, dest)

    else:
        with open(dest, 'w') as inp:
            inp.write(mol)


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

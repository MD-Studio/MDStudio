# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import json
from autobahn import wamp
from cerise_interface import (
    call_cerise_gromacs, create_cerise_config, retrieve_energies)
from lie_system import LieApplicationSession, WAMPTaskMetaData
from lie_md.settings import SETTINGS, GROMACS_LIE_SCHEMA
from md_config import set_gromacs_input

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

        # Prepare to run MD with gromacs
        files = [protein_file, ligand_file, topology_file]
        gromacs_config = set_gromacs_input(
            files, gromacs_config, workdir)

        # Cerise Configuration
        cerise_config = create_cerise_config(workdir, session)

        # Run the MD and retrieve the energies
        call_cerise_gromacs(gromacs_config, cerise_config)
        retrieve_energies(workdir)

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

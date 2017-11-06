# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

from autobahn import wamp
from cerise_interface import (
    call_cerise_gromacs, create_cerise_config, retrieve_energies)
from lie_system import LieApplicationSession, WAMPTaskMetaData
from lie_md.settings import SETTINGS
from md_config import set_gromacs_input
from pymongo import MongoClient
import os


class MDWampApi(LieApplicationSession):
    """
    Molecular dynamics WAMP methods.
    """
    db = None
    require_config = ['system']

    def __init__(self, config, package_config=None, **kwargs):

        super(MDWampApi, self).__init__(config, package_config, **kwargs)

        if self.db is None:
            host = os.getenv('MONGO_HOST', 'localhost')
            self.db = MongoClient(
                host=host, port=27017, serverSelectionTimeoutMS=1)['liestudio']

    @wamp.register(u'liestudio.gromacs.liemd')
    def run_gromacs_liemd(
            self, session={}, path_cerise_config=None,
            cwl_workflow=None, **kwargs):
        """
        Call gromacs using the Cerise-client infrastructure:
        http://cerise-client.readthedocs.io/en/master/index.html

        it expects the following keywords files for gromacs:
            * protein_pdb
            * protein_top
            * protein_itp
            * ligand_pdb
            * ligand_top
            * ligand_itp
        """
        workdir = kwargs['workdir']

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()
        session['workdir'] = workdir

        # Load GROMACS configuration and update
        gromacs_config = set_gromacs_input(
            self.package_config.dict(), workdir, kwargs)

        # Cerise Configuration
        cerise_config = create_cerise_config(
            path_cerise_config, session, cwl_workflow)

        # Run the MD and retrieve the energies
        call_cerise_gromacs(gromacs_config, cerise_config, self.db['cerise'])
        # retrieve_energies(workdir)

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

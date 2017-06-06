# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import time

from autobahn import wamp
from autobahn.wamp.types import RegisterOptions
from twisted.internet.defer import inlineCallbacks, returnValue

from lie_plants_docking.docking_settings import SETTINGS
from lie_plants_docking.plants_docking import PlantsDocking
from lie_plants_docking.utils import prepaire_work_dir
from lie_system import LieApplicationSession


class DockingWampApi(LieApplicationSession):

    """
    Docking WAMP methods.

    Defines `require_config` to retrieve system and database configuration
    upon WAMP session setup
    """

    require_config = ['system', 'lie_db']

    @inlineCallbacks
    def onRun(self, details):
        """
        Register WAMP docking methods with support for `roundrobin` load
        balancing.
        """

        # Register WAMP methods
        yield self.register(self.run_docking, u'liestudio.plants_docking.run_docking', options=RegisterOptions(invoke=u'roundrobin'))

    @wamp.register(u'liestudio.plants_docking.get')
    def retrieve_structures(self, structure_path, session=None):
        """
        Retrieve docking results structure files based on the fully qualified
        file path

        :param structure_path: fully qualified file path to the structure file
        :type structure_path:  :py:str
        :type config:   :py:class:`dict`
        """

        structure_path = '{0}.mol2'.format(structure_path)
        if os.path.isfile(structure_path):
            structure_file = None
            with open(structure_path, 'r') as sfile:
                structure_file = sfile.read()
            return {'result': structure_file}
        else:
            self.logger.error('File does not exists: {0}'.format(structure_path))
            return {'result': None}

    def check_docking(self, session=None):

        return session

    def run_docking(self, protein, ligand, session=None, **kwargs):
        """
        Perform a PLANTS (Protein-Ligand ANT System) molecular docking.

        :param protein:  protein structure
        :type protein:   string
        :param ligand:   ligand structure
        :type ligand:    string
        :param session:  call session information
        :type session:   :py:dict
        :param kwargs:   any additional keyword arguments are treated as
                         PLANTS configuration arguments
        :type kwargs:    :py:dict

        :return:         Docking results
        :rtype:          Task data construct
        """

        # Check status of running calculations
        if session.get('status', None) not in (None, 'submitted'):
            return self.check_docking(session)

        # Load PLANTS configuration and update
        plants_config = self.package_config.dict()
        plants_config.update(kwargs)

        # Run the docking
        self.logger.info('Initiate PLANTS docking', **session)

        # Prepaire docking directory
        plants_config['workdir'] = prepaire_work_dir(plants_config.get('workdir', None), user=session['authid'], create=True)

        # Run docking
        docking = PlantsDocking(user_meta=session, **plants_config)
        success = docking.run(protein, ligand)
        if success:
            session['status'] = 'DONE'
            results = docking.results()
        else:
            # Docking run not successful, cleanup
            session['status'] = 'FAILED'
            self.logger.error('PLANTS docking not successful', **session)
            docking.delete()

        self.logger.info('Finished PLANTS docking', **session)

        session['result'] = results
        return session


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
        return DockingWampApi(config, package_config=SETTINGS)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio docking management WAMPlet',
                'description': 'WAMPlet proving LIEStudio docking management endpoints'}
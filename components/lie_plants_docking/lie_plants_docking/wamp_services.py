# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import json

from twisted.internet.defer import inlineCallbacks
from lie_plants_docking.plants_docking import PlantsDocking
from lie_plants_docking.utils import prepaire_work_dir
from mdstudio.component.session import ComponentSession
from mdstudio.api.endpoint import endpoint

PLANTS_DOCKING_SCHEMA = json.load(open(plants_docking_schema))


class DockingWampApi(ComponentSession):

    """
    Docking WAMP methods.

    Defines `require_config` to retrieve system and database configuration
    upon WAMP session setup
    """

    require_config = ['system']

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

    @endpoint('docking', 'docking-request', 'docking-response')
    def run_docking(self, request, claims):
        """
        Perform a PLANTS (Protein-Ligand ANT System) molecular docking.
        For a detail description of the input see the file:
        schemas/endpoints/docking-request.v1.json
        """
        # Run the docking

        # Prepaire docking directory
        workdir = request['workdir']
        if workdir is None:
            plants_config['workdir'] = prepaire_work_dir(
                plants_config.get('workdir', None),
                user=session.get('authid', None),
                create=True)

        # Run docking
        docking = PlantsDocking(user_meta=session, **plants_config)
        success = docking.run(
            request['protein_file'], request['ligand_file'])

        if success:
            session['status'] = 'completed'
            results = docking.results()
            return {'session': session, 'output': results}
        else:
            # Docking run not successful, cleanup
            session['status'] = 'failed'
            self.logger.error('PLANTS docking not successful', **session)
            docking.delete()
            return {'session': session}

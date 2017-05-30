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

from lie_docking.docking_settings import SETTINGS
from lie_docking.plants_docking import PlantsDocking
from lie_docking.utils import prepaire_work_dir
from lie_system import LieApplicationSession, WAMPMessageEnvelope


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
        yield self.register(self.run_docking, u'liestudio.docking.run_docking', options=RegisterOptions(invoke=u'roundrobin'))

    @wamp.register(u'liestudio.docking.get')
    def retrieve_structures(self, structure_path):
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
            self.log.error('File does not exists: {0}'.format(structure_path))
            return {'result': None}

    @inlineCallbacks
    def run_docking(self, task):
        """
        Perform a molecular docking using one of the supported methods:

        * plants: PLANTS, Protein-Ligand ANT System.

        :param task:  Task session, input and configuration information
        :type task:   Task data construct

        :return:      Docking results
        :rtype:       Task data construct
        """

        # Load the task metadata into a new WAMPMessageEnvelope
        envelope = WAMPMessageEnvelope(task['_taskMeta'])

        # Load the docking task
        docking_task = task['_taskDict']

        # Run the docking
        if docking_task['_configDict'].get('method') == 'plants':
            self.log.info('Initiate docking. method: {method}', method='plants', **envelope.dict())

            # Load the input data
            protein = task['_taskDict']['proteinFile'].get('_inlineSource')

            wamp_url = task['_taskDict']['ligandFile']['_callSource']['_wamp_url']
            cid = task['_taskDict']['ligandFile']['_callSource']['_configDict']['structure_id']
            self.log.info('Retrieve ligand structure with cid {0}'.format(cid))
            ligand = yield self.call(wamp_url, cid)

            # Load configuration
            plants_config = self.package_config.get('plants').dict()
            plants_config.update(task['_taskDict']['_configDict'])

            # Prepaire docking directory
            plants_config['workdir'] = prepaire_work_dir(plants_config.get('workdir', None), user=envelope.authid, create=True)

            # Run docking
            docking = PlantsDocking(user_meta=envelope, **plants_config)
            success = docking.run(protein, ligand['result'])
            if success:
                envelope['status'] = 'DONE'
                results = docking.results()
            else:
                # Docking run not successful, cleanup
                envelope['status'] = 'FAILED'
                self.log.error('{method} not successful', method='plants', **envelope.dict())
                docking.delete()

            self.log.info('Finished docking. method: {method}', method='plants', **envelope.dict())

            returnValue({'results': results})

        else:
            self.log.error('Unsupported docking method: {0}'.format(docking_task['_configDict'].get('method'), **envelope.dict()))

        # Register job in the database
        # if self._db:
        #     docking = self._db['docking']
        #     jobid = docking.insert_one(envelope)


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

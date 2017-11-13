# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os

from autobahn import wamp

from pylie import LIEMDFrame
from lie_system import LieApplicationSession, WAMPTaskMetaData

# PYLIE_SCHEMA = json.load(open(pylie_schema))
settings = {}


class PylieWampApi(LieApplicationSession):
    """
    Pylie WAMP methods.

    Defines `require_config` to retrieve system and database configuration
    upon WAMP session setup
    """

    require_config = ['system']

    @wamp.register(u'liestudio.pylie.collect_energy_trajectories')
    def retrieve_structures(self, trajectory, filetype='gromacs', session=None):
        """
        Retrieve docking results structure files based on the fully qualified
        file path
        """

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Support multiple trajectory paths at once
        if not isinstance(trajectory, list):
            trajectory = [trajectory]

        # Collect trajectories
        mdframe = LIEMDFrame()
        for pose, trj in enumerate(trajectory):
            if not os.path.exists(trj):
                self.logger.error('File does not exists: {0}'.format(trj), **session)
                continue
            mdframe.from_file(trj, {'vdwLIE': 'vdw_bound_{0}'.format(pose + 1),
                                    'EleLIE': 'coul_bound_{0}'.format(pose + 1)}, filetype=filetype)

        # Store to file
        filepath = os.path.join(os.getcwd(), 'mdframe.csv')
        mdframe.to_csv(filepath)
        session['status'] = 'completed'

        return {'session': session, 'output': filepath}


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
        return PylieWampApi(config, package_config=settings)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio pylie management WAMPlet',
                'description': 'WAMPlet proving LIEStudio pylie management endpoints'}

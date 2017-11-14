# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import tempfile
import json
import jsonschema

from pandas import read_csv
from autobahn import wamp

from pylie import LIEMDFrame, pylie_config
from pylie.filters.filtersplines import FilterSplines
from lie_system import LieApplicationSession, WAMPTaskMetaData

pylie_schema = json.load(open(os.path.join(os.path.dirname(__file__), 'pylie_schema.json')))


class PylieWampApi(LieApplicationSession):
    """
    Pylie WAMP methods.

    Defines `require_config` to retrieve system and database configuration
    upon WAMP session setup
    """

    require_config = ['system']

    @wamp.register(u'liestudio.pylie.calculate_lie_average')
    def calculate_lie_average(self, mdframe=None, session=None, **kwargs):
        """
        Calculate LIE electrostatic and Van der Waals energy averages from
        a MDFrame.

        :param mdframe: path to LIEMDFrame
        :type mdframe:  :py:str
        :param session: WAMP session information
        :type session:  :py:dict
        """

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load MDFrame import configuration and update
        filter_config = pylie_config.get('LIEMDFrame').dict()
        filter_config.update(kwargs)

        # Validate the configuration
        jsonschema.validate(pylie_schema, filter_config)

        if not mdframe or not os.path.isfile(mdframe):
            self.logger.error('MDFrame csv file does not exist: {0}'.format(mdframe), **session)
            session['status'] = 'failed'
            return {'session': session}

        # Create workdir to save file
        workdir = os.path.join(kwargs.get('workdir', tempfile.gettempdir()))
        if not os.path.isdir(workdir):
            os.mkdir(workdir)
            self.logger.debug('Create working directory: {0}'.format(workdir), **session)

        # Import CSV file and run spline fitting filter
        liemdframe = LIEMDFrame(read_csv(mdframe))
        if 'Unnamed: 0' in liemdframe.columns:
            del liemdframe['Unnamed: 0']

        ave = liemdframe.inliers(method=filter_config.get('inlierFilterMethod', 'pair')).get_average()
        filepath = os.path.join(workdir, 'averaged.csv')
        ave.to_csv(filepath)

        output = {}
        session['status'] = 'completed'
        if os.path.isfile(filepath):
            output['averaged'] = filepath
        else:
            session['status'] = 'failed'

        output['session'] = session

        return output

    @wamp.register(u'liestudio.pylie.filter_stable_trajectory')
    def filter_stable_trajectory(self, mdframe=None, session=None, **kwargs):
        """
        Use FFT and spline-based filtering to detect and extract stable regions
        in the MD energy trajectory

        :param mdframe: path to LIEMDFrame
        :type mdframe:  :py:str
        :param session: WAMP session information
        :type session:  :py:dict
        """

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load MDFrame import configuration and update
        filter_config = pylie_config.get('FilterSplines').dict()
        filter_config.update(kwargs)

        # Validate the configuration
        jsonschema.validate(pylie_schema, filter_config)

        if not mdframe or not os.path.isfile(mdframe):
            self.logger.error('MDFrame csv file does not exist: {0}'.format(mdframe), **session)
            session['status'] = 'failed'
            return {'session': session}

        # Create workdir to save file
        workdir = os.path.join(kwargs.get('workdir', tempfile.gettempdir()))
        if not os.path.isdir(workdir):
            os.mkdir(workdir)
            self.logger.debug('Create working directory: {0}'.format(workdir), **session)

        # Import CSV file and run spline fitting filter
        liemdframe = LIEMDFrame(read_csv(mdframe))
        if 'Unnamed: 0' in liemdframe.columns:
            del liemdframe['Unnamed: 0']

        splines = FilterSplines(liemdframe, **filter_config)
        liemdframe = splines.filter()

        output = {}
        # Report the selected stable regions
        filtered = liemdframe.inliers()
        for pose in filtered.poses:
            stable = filtered.get_stable(pose)
            if stable:
                output['stable_pose_{0}'.format(pose)] = stable

        # Create plots
        if filter_config.get('do_plot', False):
            currpath = os.getcwd()
            os.chdir(workdir)
            splines.plot(tofile=True, filetype=filter_config.get('plotFileType', 'pdf'))
            os.chdir(currpath)

        # Filter the mdframe
        if filter_config.get('do_filter', True):
            filepath = os.path.join(workdir, 'mdframe_splinefiltered.csv')
            filtered.to_csv(filepath)

            if os.path.isfile(filepath):
                output['filtered_mdframe'] = filepath

        session['status'] = 'completed'
        output['session'] = session

        return output

    @wamp.register(u'liestudio.pylie.collect_energy_trajectories')
    def import_mdene_files(self, bound_trajectory=None, unbound_trajectory=None, session=None, **kwargs):
        """
        Import GROMACS MD trajectory energy files into a LIEMDFrame

        :param bound_trajectory: one or multiple Gromacs energy trajectory
                                 file paths for bound systems
        :param unbound_trajectory: one or multiple Gromacs energy trajectory
                                 file paths for unbound systems
        :param session:          WAMP session information
        :type session:           :py:dict
        """

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load MDFrame import configuration and update
        mdframe_config = pylie_config.get('LIEMDFrame').dict()
        mdframe_config.update(kwargs)

        # Validate the configuration
        jsonschema.validate(pylie_schema, mdframe_config)

        # Create workdir to save file
        workdir = os.path.join(kwargs.get('workdir', tempfile.gettempdir()))
        if not os.path.isdir(workdir):
            os.mkdir(workdir)
            self.logger.debug('Create working directory: {0}'.format(workdir), **session)

        # Support multiple trajectory paths at once
        if not isinstance(bound_trajectory, list):
            bound_trajectory = [bound_trajectory]
        if not isinstance(unbound_trajectory, list):
            unbound_trajectory = [unbound_trajectory]

        # Collect trajectories
        mdframe = LIEMDFrame()
        vdw_header = mdframe_config.get('lie_vdw_header', 'vdwLIE')
        ele_header = mdframe_config.get('lie_ele_header', 'EleLIE')
        for pose, trj in enumerate(bound_trajectory):
            if not os.path.exists(trj):
                self.logger.error('File does not exists: {0}'.format(trj), **session)
                continue
            mdframe.from_file(trj, {vdw_header: 'vdw_bound_{0}'.format(pose + 1),
                                    ele_header: 'coul_bound_{0}'.format(pose + 1)},
                              filetype=mdframe_config['filetype'])
            self.logger.debug('Import file: {0}, pose: {1}'.format(trj, pose))

        for trj in unbound_trajectory:
            if not os.path.exists(trj):
                self.logger.error('File does not exists: {0}'.format(trj), **session)
                continue
            mdframe.from_file(trj, {vdw_header: 'vdw_unbound', ele_header: 'coul_unbound'},
                              filetype=mdframe_config['filetype'])
            self.logger.debug('Import unbound file: {0}'.format(trj))

        # Set the case ID
        mdframe.case = mdframe_config.get('case', 1)

        # Store to file
        filepath = os.path.join(workdir, 'mdframe.csv')
        mdframe.to_csv(filepath)

        session['status'] = 'completed'

        return {'session': session, 'mdframe': filepath}


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
        return PylieWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio pylie management WAMPlet',
                'description': 'WAMPlet proving LIEStudio pylie management endpoints'}

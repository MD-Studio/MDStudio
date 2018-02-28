# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import tempfile
import json
import pickle

from pandas import (read_csv, read_json, read_excel, read_table, concat, DataFrame)
from autobahn import wamp

from pylie import LIEMDFrame, LIEDataFrame, pylie_config
from pylie.filters.filtersplines import FilterSplines
from pylie.filters.filtergaussian import FilterGaussian
from pylie.methods.adan import ad_residue_decomp, ad_dene, ad_dene_yrange, parse_gromacs_decomp
from mdstudio.api.endpoint import endpoint
from mdstudio.component.session import ComponentSession

pylie_schema = json.load(open(os.path.join(os.path.dirname(__file__), 'pylie_schema.json')))

PANDAS_IMPORTERS = {'csv': read_csv, 'json': read_json, 'xlsx': read_excel, 'tbl': read_table}
PANDAS_EXPORTERS = {'csv': 'to_csv', 'json': 'to_json', 'xlsx': 'to_excel', 'tbl': 'to_string'}


class PylieWampApi(ComponentSession):
    """
    Pylie WAMP methods.

    Defines `require_config` to retrieve system and database configuration
    upon WAMP session setup
    """
    def authorize_request(self, uri, claims):
        return True

    def _get_config(self, config, name):

        ref_config = pylie_config.get(name).dict()
        ref_config.update(config)

        return ref_config

    def _import_to_dataframe(self, infile):

        if not os.path.isfile(infile):
            self.log.error('No such file: {0}'.format(infile))
            return

        ext = infile.split('.')[-1]
        if ext not in PANDAS_IMPORTERS:
            self.log.error('Unsupported file format: {0}'.format(ext))
            return

        df = PANDAS_IMPORTERS[ext](infile)
        if 'Unnamed: 0' in df:
            del df['Unnamed: 0']

        return df

    def _export_dataframe(self, df, outfile, file_format='csv'):

        if file_format not in PANDAS_EXPORTERS:
            self.log.error('Unsupported file format: {0}'.format(file_format))
            return False

        if hasattr(df, PANDAS_EXPORTERS[file_format]):
            method = getattr(df, PANDAS_EXPORTERS[file_format])

            # Export to file
            with open(outfile, 'w') as outf:
                method(outf)

            return True
        return False

    @endpoint('liedeltag', 'liedeltag_request', 'liedeltag_response')
    def calculate_lie_deltag(self, request, claims):
        """
        For a detailed input description see:
          pylie/schemas/endpoints/liedeltag_request.json

        For a detailed output description see:
          pylie/schemas/endpoints/liedeltag_response.json
        """
        alpha_beta_gamma = request['alpha_beta_gamma']

        # Filter DataFrame
        dfobject = LIEDataFrame(self._import_to_dataframe(request['dataframe']))
        dg_calc = dfobject.liedeltag(params=alpha_beta_gamma, kBt=request['kBt'])

        # Create workdir to save file
        workdir = os.path.join(request['workdir'], tempfile.gettempdir())
        if not os.path.isdir(workdir):
            os.mkdir(workdir)
            self.logger.debug('Create working directory: {0}'.format(workdir))

        # Save dataframe
        file_format = request['file_format']
        filepath = os.path.join(workdir, 'liedeltag.{0}'.format(file_format))
        if self._export_dataframe(dg_calc, filepath, file_format=file_format):
            status = 'completed'
            results = dg_calc.to_dict()
        else:
            status = 'failed'
            filepath = None
            results = None

            return {'status': status, 'liedeltag_file': filepath, 'liedeltag': results}

    @wamp.register(u'liestudio.pylie.concat_dataframes')
    def concat_dataframes(self, request, claims):
        """
        Combine multiple tabular DataFrames into one new DataFrame using
        the Python Pandas library.

        For a detailed input description see:
          pylie/schemas/endpoints/concat_dataframes_request.json

        For a detailed output description see:
          pylie/schemas/endpoints/concat_dataframes_response.json
        """
        # Import all files
        dfs = []
        for dataframe in request['dataframes']:
            dfobject = self._import_to_dataframe(dataframe)
            if isinstance(dfobject, DataFrame):
                dfs.append(dfobject)

        # Concatenate dataframes
        if len(dfs) > 1:
            concat_df = concat(
                dfs, ignore_index=request['ignore_index'],
                axis=request['axis'], join=request['join'])

            status = 'completed'

            # Create workdir to save file
            workdir = os.path.join(request['workdir'], tempfile.gettempdir())
            if not os.path.isdir(workdir):
                os.mkdir(workdir)
                self.logger.debug('Create working directory: {0}'.format(workdir))

            file_format = request['file_format']
            filepath = os.path.join(workdir, 'joined.{0}'.format(file_format))
            if self._export_dataframe(concat_df, filepath, file_format=file_format):
                concat_mdframe = filepath
        else:
            status = 'failed'
            concat_mdframe = None

        return {'status': status, 'concat_mdframe': concat_mdframe}

    @endpoint('calculate_lie_average', 'calculate_lie_average_request', 'calculate_lie_average_response')
    def calculate_lie_average(self, request, claims):
        """
        Calculate LIE electrostatic and Van der Waals energy averages from
        a MDFrame.

        For a detailed input description see:
          pylie/schemas/endpoints/calculate_lie_average_request.v1.json

        For a detailed output description see:
          pydlie/schemas/endpoints/calculate_lie_average_response.v1.json
        """
        mdframe = request['mdframe']

        if not os.path.isfile(mdframe):
            self.logger.error('MDFrame csv file does not exist: {0}'.format(mdframe))
            status = 'failed'
            return {'status': status, 'averaged': None}

        # Create workdir to save file
        workdir = os.path.join(request['workdir'], tempfile.gettempdir())
        if not os.path.isdir(workdir):
            os.mkdir(workdir)
            self.logger.debug('Create working directory: {0}'.format(workdir))

        # Import CSV file and run spline fitting filter
        liemdframe = LIEMDFrame(read_csv(mdframe))
        if 'Unnamed: 0' in liemdframe.columns:
            del liemdframe['Unnamed: 0']

        ave = liemdframe.inliers(method=request['inlierFilterMethod']).get_average()
        filepath = os.path.join(workdir, 'averaged.csv')
        ave.to_csv(filepath)

        if os.path.isfile(filepath):
            status = 'completed'
            averaged = filepath
        else:
            status = 'failed'
            averaged = None

        return {'status': status, 'averaged': averaged}

    @endpoint('gaussian_filter', 'gaussian_filter_request', 'gaussian_filter_response')
    def filter_gaussian(self, request, claims):
        """
        Use multivariate Gaussian Distribution analysis to
        filter VdW/Elec values

        For a detailed input description see:
          pylie/schemas/endpoints/gaussian_filter_request.v1.json

        For a detailed output description see:
          pydlie/schemas/endpoints/gaussian_filter_response.v1.json
        """
        # Filter DataFrame
        dfobject = LIEDataFrame(
            self._import_to_dataframe(request['dataframe']))
        gaussian = FilterGaussian(
            dfobject, confidence=request["confidence"])
        filtered = gaussian.filter()
        self.log.info("Filter detected {0} outliers.".format(len(filtered.outliers.cases)))

        # Create workdir to save file
        workdir = os.path.join(request['workdir'], tempfile.gettempdir())
        if not os.path.isdir(workdir):
            os.mkdir(workdir)
            self.log.debug('Create working directory: {0}'.format(workdir))

        # Plot results
        if request['plot']:
            outp = os.path.join(workdir, 'gauss_filter.pdf')
            p = gaussian.plot()
            p.savefig(outp)

        # Save filtered dataframe
        file_format = request['file_format']
        filepath = os.path.join(workdir, 'gauss_filter.{0}'.format(file_format))
        if self._export_dataframe(
                filtered, filepath, file_format=file_format):
            status = 'completed'
        else:
            status = 'failed'
            filepath = None

        return {'status': status, 'gauss_filter': filepath}

    @endpoint('filter_stable', 'filter_stable_request', 'filter_stable_request')
    def filter_stable_trajectory(self, request, claims):
        """
        Use FFT and spline-based filtering to detect and extract stable regions
        in the MD energy trajectory

        For a detailed input description see:
          pylie/schemas/endpoints/filter_stable_request.v1.json

        For a detailed output description see:
          pydlie/schemas/endpoints/filter_stable_response.v1.json
        """
        mdframe = request['mdframe']
        if not os.path.isfile(mdframe):
            self.logger.error('MDFrame csv file does not exist: {0}'.format(mdframe))
            return {'status': 'failed', 'output': None}

        # Create workdir to save file
        workdir = os.path.join(request['workdir'], tempfile.gettempdir())
        if not os.path.isdir(workdir):
            os.mkdir(workdir)
            self.log.debug('Create working directory: {0}'.format(workdir))

        # Import CSV file and run spline fitting filter
        liemdframe = LIEMDFrame(read_csv(mdframe))
        if 'Unnamed: 0' in liemdframe.columns:
            del liemdframe['Unnamed: 0']

        splines = FilterSplines(liemdframe, request['FilterSplines'])
        liemdframe = splines.filter()

        output = {}
        # Report the selected stable regions
        filtered = liemdframe.inliers()
        for pose in filtered.poses:
            stable = filtered.get_stable(pose)
            if stable:
                output['stable_pose_{0}'.format(pose)] = stable

        # Create plots
        if request['do_plot']:
            currpath = os.getcwd()
            os.chdir(workdir)
            splines.plot(tofile=True, filetype=request['plotFileType'])
            os.chdir(currpath)

        # Filter the mdframe
        if request['do_filter']:
            filepath = os.path.join(workdir, 'mdframe_splinefiltered.csv')
            filtered.to_csv(filepath)

            if os.path.isfile(filepath):
                output['filtered_mdframe'] = filepath

        return {'status': 'completed', 'output': output}

    @wamp.register(u'liestudio.pylie.collect_energy_trajectories')
    def import_mdene_files(self, bound_trajectory=None, unbound_trajectory=None, session=None, **kwargs):
        """
        Import GROMACS MD trajectory energy files into a LIEMDFrame.

        The constructed LIEMDFrame should represents simulations for the same
        system with one simulation for the unbound state of the ligand and one
        or more simulations for the bound system with the ligand in potentially
        multiple binding poses.

        For a detailed input description see:
          pylie/schemas/endpoints/collect_energies_request.v1.json

        For a detailed output description see:
          pydlie/schemas/endpoints/collect_energies_response.v1.json
        """
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
                self.log.error('File does not exists: {0}'.format(trj), **session)
                continue
            mdframe.from_file(trj, {vdw_header: 'vdw_bound_{0}'.format(pose + 1),
                                    ele_header: 'coul_bound_{0}'.format(pose + 1)},
                              filetype=mdframe_config['filetype'])
            self.log.debug('Import file: {0}, pose: {1}'.format(trj, pose))

        for trj in unbound_trajectory:
            if not os.path.exists(trj):
                self.logger.error('File does not exists: {0}'.format(trj), **session)
                continue
            mdframe.from_file(trj, {vdw_header: 'vdw_unbound', ele_header: 'coul_unbound'},
                              filetype=mdframe_config['filetype'])
            self.log.debug('Import unbound file: {0}'.format(trj))

        # Set the case ID
        mdframe.case = mdframe_config.get('case', 1)

        # Store to file
        filepath = os.path.join(workdir, 'mdframe.csv')
        mdframe.to_csv(filepath)

        session['status'] = 'completed'

        return {'session': session, 'mdframe': filepath}

    @wamp.register(u'liestudio.pylie.adan_residue_decomp')
    def adan_residue_decomp(self, decomp_files=None, model_pkl=None, cases=None, session=None, **kwargs):

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load the model
        if not os.path.isfile(model_pkl):
            self.log.error('eTOX model file does not exist: {0}'.format(model_pkl))
            session['status'] = 'failed'
            return {'session': session}

        model = pickle.load(open(model_pkl))

        # Parse gromacs residue decomposition energy files to DataFrame
        decomp_dfs = []
        for dcfile in decomp_files:
            decomp_dfs.append(parse_gromacs_decomp(dcfile))

        # Run AD test
        ene = ad_residue_decomp(decomp_dfs, model['AD']['decVdw'], model['AD']['decEle'], cases=cases)

        # Create workdir and save file
        workdir = os.path.join(kwargs.get('workdir', None))
        if workdir:
            if not os.path.isdir(workdir):
                os.mkdir(workdir)
                self.log.debug('Create working directory: {0}'.format(workdir), **session)
            filepath = os.path.join(workdir, 'adan_residue_decomp.csv')
            ene.to_csv(filepath)

        session['status'] = 'completed'
        return {'session': session, 'decomp': ene.to_dict()}

    @wamp.register(u'liestudio.pylie.adan_dene')
    def adan_dene(self, dataframe=None, model_pkl=None, center=None, ci_cutoff=None, session=None, **kwargs):

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load the model
        if not os.path.isfile(model_pkl):
            self.log.error('eTOX model file does not exist: {0}'.format(model_pkl))
            session['status'] = 'failed'
            return {'session': session}

        model = pickle.load(open(model_pkl))

        # Parse gromacs residue decomposition energy files to DataFrame
        dfobject = self._import_to_dataframe(dataframe)

        # Run AD test
        ene = ad_dene(dfobject, model['AD']['Dene']['CovMatrix'], center=center, ci_cutoff=ci_cutoff)

        # Create workdir and save file
        workdir = os.path.join(kwargs.get('workdir', None))
        if workdir:
            if not os.path.isdir(workdir):
                os.mkdir(workdir)
                self.log.debug('Create working directory: {0}'.format(workdir), **session)
            filepath = os.path.join(workdir, 'adan_dene.csv')
            ene.to_csv(filepath)

        session['status'] = 'completed'
        return {'session': session, 'decomp': ene.to_dict()}

    @wamp.register(u'liestudio.pylie.adan_dene_yrange')
    def adan_dene_yrange(self, dataframe=None, ymin=None, ymax=None, session=None, **kwargs):

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Parse gromacs residue decomposition energy files to DataFrame
        dfobject = self._import_to_dataframe(dataframe)

        # Run AD test
        ene = ad_dene_yrange(dfobject, ymin, ymax)

        # Create workdir and save file
        workdir = os.path.join(kwargs.get('workdir', None))
        if workdir:
            if not os.path.isdir(workdir):
                os.mkdir(workdir)
                self.log.debug('Create working directory: {0}'.format(workdir), **session)
            filepath = os.path.join(workdir, 'adan_dene_yrange.csv')
            ene.to_csv(filepath)

        session['status'] = 'completed'
        return {'session': session, 'decomp': ene.to_dict()}

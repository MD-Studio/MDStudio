# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import jsonschema
import pkg_resources
import logging
import tempfile
import MDAnalysis as mda

from propka import molecular_container
from propkatraj import get_propka
from autobahn.wamp.types import RegisterOptions
from twisted.internet.defer import inlineCallbacks
from lie_system import LieApplicationSession, WAMPTaskMetaData

from . import settings, propka_schema
from .propka_helpers import parse_propka_pkaoutput


class Struct:

    def __init__(self, entries):
        self.__dict__.update(entries)


class RunPropka(object):

    def run_propkatraj(self, topology=None, trajectory=None, sel='protein',
                       start=None, stop=None, step=None, session=None):
        """
        Run propkatraj

        Runs Propka3.1 on a MD trajectory in a format that can be handled by
        the MDanalysis package

        :param kwargs:  PROPKA options
        :type kwargs:   :py:dict
        :param session: WAMP session object
        :type session:  :py:dict

        :return:        PROPKA results
        :rtype:         :py:dict
        """

        # Load WAMP session if any
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load trajectory
        universe = mda.Universe(topology, trajectory)

        # Run propkatraj
        pkatrajdf = get_propka(universe, sel=sel, start=start, stop=stop, step=step)

        return {'session': session}

    def run_propka(self, session=None, **kwargs):
        """
        Run PROPKA

        :param kwargs:  PROPKA options
        :type kwargs:   :py:dict
        :param session: WAMP session object
        :type session:  :py:dict

        :return:        PROPKA results
        :rtype:         :py:dict
        """

        # Load WAMP session if any
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load PROPKA configuration file
        propka_config = kwargs
        if not propka_config.get('parameters'):
            propka_config['parameters'] = pkg_resources.resource_filename("propka", "propka.cfg")

        # Validate against JSON schema
        jsonschema.validate(propka_config, propka_schema)

        # Update with JSON settings
        for k, v in settings.items():
            if k not in propka_config:
                propka_config[k] = v

        # Parse titration
        if propka_config.get('titrate_only'):
            newtitr = []
            for titr in propka_config['titrate_only'].split(','):
                chain, resnum_str = titr.split(":")
                newtitr.append((chain, int(resnum_str), " "))
            propka_config['titrate_only'] = newtitr

        # Create workdir and save file
        currdir = os.getcwd()
        workdir = os.path.join(kwargs.get('workdir', tempfile.gettempdir()))
        if not os.path.isdir(workdir):
            os.makedirs(workdir)
        os.chdir(workdir)
        logging.info('PropKa working directory: {0}'.format(workdir))

        if propka_config.get('from_file', False):
            pdbfile = os.path.join(workdir, 'propka.pdb')
            with open(pdbfile) as infile:
                infile.write(propka_config.get('pdb'))
        else:
            pdbfile = propka_config.get('pdb')

        # Wrap options dictionary as object (needed for PROPKA)
        propka_config = Struct(propka_config)

        # Run PROPKA
        my_molecule = molecular_container.Molecular_container(pdbfile, propka_config)
        my_molecule.calculate_pka()
        my_molecule.write_pka()
        logging.info('Running PROPKA 3.1: {0}'.format(type(my_molecule.version).__name__.split('.')[-1]))

        # Parse PROPKA output
        output_dict = {}
        for output_types in ('pka', 'propka_input'):
            outputfile = os.path.join(workdir, '{0}.{1}'.format(my_molecule.name, output_types))

            if not os.path.isfile(outputfile):
                logging.error('Propka failed to create output: {0}'.format(outputfile))
                continue

            if output_types == 'pka':
                pkadf = parse_propka_pkaoutput(outputfile)
                output_dict['pka'] = pkadf.to_dict()
                session['status'] = 'completed'

            output_dict['{0}_file'.format(output_types)] = outputfile

        # Calculate molecule PI
        pi_labels = ('pi_folded', 'pi_unfolded')
        for i, pi in enumerate(my_molecule.getPI()):
            output_dict[pi_labels[i]] = pi

        # Change back to original dir and return results
        output_dict['session'] = session
        os.chdir(currdir)
        return output_dict


class PropkaWampApi(LieApplicationSession, RunPropka):

    @inlineCallbacks
    def onRun(self, details):
        """
        Register WAMP docking methods with support for `roundrobin` load
        balancing.
        """

        # Register WAMP methods
        yield self.register(self.run_propka, u'liestudio.propka.run_propka',
                            options=RegisterOptions(invoke=u'roundrobin'))


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
        return PropkaWampApi(config, package_config=settings)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {
            'label': 'LIEStudio PropKa WAMPlet',
            'description':
            'WAMPlet proving LIEStudio PropKa endpoints'}
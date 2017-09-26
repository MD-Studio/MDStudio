# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import json
import jsonschema

from autobahn import wamp

from lie_system import LieApplicationSession, WAMPTaskMetaData
from lie_structures import settings, structures_schema
from lie_structures.cheminfo_utils import (
    mol_addh, mol_attributes, mol_make3D, mol_read, mol_removeh, mol_write)

STRUCTURES_SCHEMA = json.load(open(structures_schema))


class StructuresWampApi(LieApplicationSession):
    """
    Structure database WAMP methods.
    """

    require_config = ['system']

    # @inlineCallbacks
    # def onJoin(self, details):
    #
    #     yield self.register(self.get_structure, u'liestudio.structures.get_structure', options=RegisterOptions(invoke=u'roundrobin'))
    #     self.log.info("StructuresWampApi: get_structure() registered!")

    @wamp.register(u'liestudio.structures.get_structure')
    def get_structure(self, structure=None, session={}, **kwargs):

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session)

        result = ''
        tmpdir = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/tmp'
        structure_file = os.path.join(tmpdir, structure)
        if os.path.exists(structure_file):
            with open(structure_file, 'r') as sf:
                result = sf.read()
        else:
            self.log.error("No such file {0}".format(structure_file))

        self.log.info(
            "Return structure: {structure}",
            structure=structure, **self.session_config.dict())

        # Pack result in session
        session.status = 'completed'
        return {'session': session.dict(), 'structure': result}

    @wamp.register(u'liestudio.structure.convert')
    def convert_structures(self, session={}, **kwargs):
        """
        Convert input file format to a different format
        """

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load configuration and update
        config = self.package_config.lie_structures.dict()
        config.update(kwargs)

        # Validate against JSON schema
        jsonschema.validate(config, STRUCTURES_SCHEMA)

        molobject = mol_read(
            config['mol'], mol_format=config.get('input_format'))
        output = mol_write(
            molobject,  mol_format=config.get('output_format'))

        # Update session
        session['status'] = 'completed'

        return {'mol': output, 'session': session}

    @wamp.register(u'liestudio.structure.addh')
    def addh_structures(self, session={},  **kwargs):
        """
        Add hydrogens to the input structure
        """

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load configuration and update
        config = self.package_config.lie_structures.dict()
        config.update(kwargs)

        # Validate against JSON schema
        jsonschema.validate(config, STRUCTURES_SCHEMA)

        molobject = mol_read(
            config['mol'], mol_format=config.get('input_format'))
        molobject = mol_addh(
            molobject,
            polaronly=config.get('polaronly'),
            correctForPH=config.get('correctForPH'),
            pH=config.get('pH'))

        output = mol_write(
            molobject, mol_format=config.get('output_format'))

        # Update session
        session['status'] = 'completed'

        return {'mol': output, 'session': session}

    @wamp.register(u'liestudio.structure.removeh')
    def removeh_structures(self, session={},  **kwargs):
        """
        Remove hydrogens from the input structure
        """

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load configuration and update
        config = self.package_config.lie_structures.dict()
        config.update(kwargs)

        # Validate against JSON schema
        jsonschema.validate(config, STRUCTURES_SCHEMA)

        molobject = mol_read(
            config['mol'], mol_format=config.get('input_format'))
        molobject = mol_removeh(
            molobject)

        output = mol_write(
            molobject, mol_format=config.get('output_format'))

        # Update session
        session['status'] = 'completed'

        return {'mol': output, 'session': session}

    @wamp.register(u'liestudio.structure.make3d')
    def make3d_structures(self, session={},  **kwargs):
        """
        Convert 1D or 2D structure representation to 3D
        """

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load configuration and update
        config = self.package_config.lie_structures.dict()
        config.update(kwargs)

        # Validate against JSON schema
        jsonschema.validate(config, STRUCTURES_SCHEMA)

        molobject = mol_read(
            config['mol'], mol_format=config.get('input_format'))
        molobject = mol_make3D(
            molobject,
            forcefield=config.get('forcefield'),
            localopt=config.get('localopt', True),
            steps=config.get('steps', 50))

        output = mol_write(
            molobject, mol_format=config.get('output_format'))

        # Update session
        session['status'] = 'completed'

        return {'mol': output, 'session': session}

    @wamp.register(u'liestudio.structure.info')
    def structure_attributes(self, session={}, **kwargs):
        """
        Return common structure attributes
        """

        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=session).dict()

        # Load configuration and update
        config = self.package_config.lie_structures.dict()
        config.update(kwargs)

        # Validate against JSON schema
        jsonschema.validate(config, STRUCTURES_SCHEMA)

        molobject = mol_read(
            config['mol'], mol_format=config.get('input_format'))
        attributes = mol_attributes(molobject) or {}

        # Update session
        session['status'] = 'completed'
        attributes['session'] = session

        return attributes


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
        return StructuresWampApi(config, package_config=settings)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {
            'label': 'LIEStudio structure management WAMPlet',
            'description':
            'WAMPlet proving LIEStudio structure management endpoints'}

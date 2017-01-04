# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import time

from   autobahn import wamp
from   autobahn.wamp.types import RegisterOptions
from   twisted.internet.defer import inlineCallbacks

from   lie_system  import LieApplicationSession

class StructuresWampApi(LieApplicationSession):

    """
    Structure database WAMP methods.
    """
    
    @inlineCallbacks
    def onJoin(self, details):
        yield self.register(self.get_structure, u'liestudio.structures.get_structure', options=RegisterOptions(invoke=u'roundrobin'))
        self.log.info("DockingWampApi: get_structure() registered!")
    
    def get_structure(self, structure):
        
        result = ''
        currpath = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/components/lie_structures-0.1/lie_structures'
        structure_file = os.path.join(currpath, '{0}.mol2'.format(structure))
        if os.path.exists(structure_file):
            with open(structure_file, 'r') as sf:
                result = sf.read()
        
        self.log.info("Return structure: {structure}", structure=structure_file, **self.session_config.dict())
        
        return {'result': result}

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
        return StructuresWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio structure management WAMPlet',
                'description': 'WAMPlet proving LIEStudio structure management endpoints'}
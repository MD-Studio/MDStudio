# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import time
import json
import re

from   autobahn               import wamp
from   twisted.internet.defer import inlineCallbacks
from   twisted.internet       import reactor

from   lie_system             import LieApplicationSession

class TopologyWampApi(LieApplicationSession):
    
    @wamp.register(u'liestudio.topology.parse_structure')
    def topology_parse_structure( self, pdb_path, ftype="auto" ):
        
        """
        Submit a new calculation to the ATB server
        
        :param pdb_path:  path to a structure file
        :type pdb_path:   :py:str
        :param ftype:     file type, auto means detect from the extension
        :type ftype:      :py:str
        """
        
        self.logger.error('Topology.parse_structure not in use yet')
     
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
        return TopologyWampApi(config, package_config=SETTINGS)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio topology interface WAMPlet',
                'description': 'WAMPlet providing LIEStudio connectivity to topology parsing and writing'}
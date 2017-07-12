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
from lie_componentbase import BaseApplicationSession
from   twisted.internet.defer import inlineCallbacks

from   lie_amber              import *

class AmberWampApi(BaseApplicationSession):
    """
    AmberTools WAMP methods.
    """
    
    require_config = ['system']
    
    @wamp.register(u'liestudio.amber.acpype')
    def run_amber_acpype(self, mol, session=None, **kwargs):
        
        # Load ACPYPE configuration and update
        acpype_config = self.package_config.get('amber_acpype')
        acpype_config.update(kwargs)
        
        # Run ACPYPE
        output = amber_acpype(mol, **acpype_config)
        if not output:
            session['status'] = 'FAILED'
        else:
            session['status'] = 'DONE'
            session['result'] = output
            
        return session
        
def make(config):
    """
    Component factory
  
    This component factory creates instances of the application component
    to run.
    
    The function will get called either during development using an 
    ApplicationRunner, or as a plugin hosted in a WAMPlet container such as
    a Crossbar.io worker.
    The BaseApplicationSession class is initiated with an instance of the
    ComponentConfig class by default but any class specific keyword arguments
    can be consument as well to populate the class session_config and
    package_config dictionaries.
    
    :param config: Autobahn ComponentConfig object
    """
    
    if config:
        return AmberWampApi(config, package_config=SETTINGS)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio AmberTools interface WAMPlet',
                'description': 'WAMPlet providing LIEStudio connectivity to the AmberTools software suite'}
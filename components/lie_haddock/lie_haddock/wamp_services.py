# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import time

from   autobahn                            import wamp
from   autobahn.wamp.types                 import RegisterOptions
from   twisted.internet.defer              import inlineCallbacks

from   lie_componentbase                          import BaseApplicationSession

class HaddockWampApi(BaseApplicationSession):
    """
    HADDOCK docking WAMP methods.
    
    Defines `require_config` to retrieve system and database configuration
    upon WAMP session setup 
    """
    
    require_config = ['system', 'lie_db']
    
    @wamp.register(u'liestudio.haddock_docking.get')
    def retrieve_haddock_project(self, project_name, session=None):
        """
        Retrieve the docking results as tar zipped archive
        
        :param project_name: HADDOCK web server project name
        :type project_name:  :py:str
        """
    
    @wamp.register(u'liestudio.haddock_docking.status')
    def haddock_project_status(self, project_name, session=None):
        """
        Retrieve the status of a submitted haddock project
        
        :param project_name: HADDOCK web server project name
        :type project_name:  :py:str
        """
    
    @wamp.register(u'liestudio.haddock_docking.submit')
    def submit_haddock_project(self, project_name, session=None):
        """
        Submit a docking project to the HADDOCK web server
        
        :param project_name: HADDOCK web server project name
        :type project_name:  :py:str
        """
        
    
            
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
        return HaddockWampApi(config, package_config=SETTINGS)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio HADDOCK docking web server WAMPlet',
                'description': 'WAMPlet proving access to the HADDOCK dockign web server'}
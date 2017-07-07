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

from   lie_workflow                        import Workflow
from   lie_componentbase                          import BaseApplicationSession


class WorkflowWampApi(BaseApplicationSession):
    """
    Workflow WAMP methods.
    
    Defines `require_config` to retrieve system and database configuration
    upon WAMP session setup 
    """
    
    require_config = ['system', 'lie_db']
    
    @wamp.register(u'liestudio.workflow.run')
    def retrieve_structures(self, workflow, session=None):
        """
        Run a LIE Workflow
        """
        
        print(workflow)
        print(session)
        
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
        return WorkflowWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio workflow management WAMPlet',
                'description': 'WAMPlet proving LIEStudio workflow management endpoints'}
# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""
  
from   autobahn               import wamp
from   twisted.internet.defer import inlineCallbacks

from   lie_componentbase             import BaseApplicationSession

class ScriptRunnerWampApi(BaseApplicationSession):
    """
    Script runner WAMP methods
    """
    
    @wamp.register(u'liestudio.scriptrunner.shell')
    def shell_script_runner(self, script, session=None):
        """
        Submit a new calculation to the ATB server
        
        :param script:  Shell script to run
        :type script:   :py:str
        """
        
        # Return dummy data
        session['status'] = 'done'
        session['result'] = 'shell data'
        
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
        return ScriptRunnerWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio script runner WAMPlet',
                'description': 'WAMPlet enabling LIEStudio to run custom scripts'}
# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import time
import json

from   autobahn               import wamp
from   twisted.internet.defer import inlineCallbacks

from   lie_system import LieApplicationSession
from   lie_config import get_config

class ConfigWampApi(LieApplicationSession):
    """
    Configuration management WAMP methods.
    """
       
    @wamp.register(u'liestudio.config.get')
    def getConfig(self, key, config='default'):
        """
        Retrieve application configuration.
    
        Search for `key` anywhere in a globally accessible 
        configuration store. 
        Returns query results in JSON format
        """
    
        settings = self.package_config.search('*{0}*'.format(str(key)))
        return settings.dict()
    
    @inlineCallbacks
    def onJoin(self, details):
        res = yield self.register(self)
        self.logging.debug("ConfigBackend: {} procedures registered!".format(len(res)))

def make(config):
    """
    Component factory
  
    This component factory creates instances of the
    application component to run.
    
    The function will get called either during development
    using the ApplicationRunner below, or as  a plugin running
    hosted in a WAMPlet container such as a Crossbar.io worker.
    """
    
    if config:
        return ConfigWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio configuration management WAMPlet',
                'description': 'WAMPlet proving LIEStudio configuration management endpoints'}
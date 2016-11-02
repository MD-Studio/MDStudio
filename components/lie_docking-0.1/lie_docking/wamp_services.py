# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import time
import random

from   autobahn.wamp.types import RegisterOptions
from   twisted.internet.defer import inlineCallbacks, returnValue

from   lie_docking import settings
from   lie_system  import LieApplicationSession

class DockingWampApi(LieApplicationSession):

    """
    Docking WAMP methods.
    """
       
    @inlineCallbacks
    def onRun(self, details):
        
        yield self.register(self.docking_run, u'liestudio.docking.run', options=RegisterOptions(invoke=u'roundrobin'))
        
    def docking_run(self, protein, ligand, method='plants', **kwargs):
        """
        Perform a docking run using one of the available methods
        
        :param protein: protein 3D structure file
        :type protein:  str
        :param ligand:  ligand 3D structure file
        :type ligand:   str
        :param method:  docking method to use
        :type method:   str
        """
        
        self.log.info('Initiate docking. method: {method}', method=method, **self.session_config)
        
        if method == "plants":
            from plants_docking import PlantsDocking
            
            # TODO: lie_docking should not be the toplevel dictionary attribute
            plants_config = self.package_config.lie_docking.plants.dict()
            plants_config.update(kwargs)
            
            workdir = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/docking_{0}'.format(random.randint(1,1000))
            docking = PlantsDocking(workdir, **plants_config)
            docking.run(protein, ligand)
            results = docking.results()
        
        self.log.info('Finished docking. method: {method}', method=method, **self.session_config)
            
        return {'result': results}

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
        return DockingWampApi(config, package_config=settings)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio docking management WAMPlet',
                'description': 'WAMPlet proving LIEStudio docking management endpoints'}
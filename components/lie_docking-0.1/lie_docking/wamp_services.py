# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import time

from   autobahn.wamp.types          import RegisterOptions
from   twisted.internet.defer       import inlineCallbacks, returnValue

from   lie_docking                  import settings
from   lie_docking.plants_docking   import PlantsDocking
from   lie_docking.utils            import prepaire_work_dir
from   lie_system                   import LieApplicationSession

class DockingWampApi(LieApplicationSession):

    """
    Docking WAMP methods.
    """
       
    @inlineCallbacks
    def onRun(self, details):
        
        yield self.register(self.plants_docking, u'liestudio.docking.plants', options=RegisterOptions(invoke=u'roundrobin'))
    
    def plants_docking(self, protein, ligand, config={}):
        """
        Perform a PLANTS based docking run
        
        :param protein: protein 3D structure file
        :type protein:  str
        :param ligand:  ligand 3D structure file
        :type ligand:   str
        :param config:  docking method configuration options
        :type config:   :py:class:`dict`
        """
        
        self.log.info('Initiate docking. method: {method}', method='plants', **self.session_config)
        
        plants_config = self.package_config.plants.dict()
        plants_config.update(config)
        
        # Prepaire docking directory
        plants_config['workdir'] = prepaire_work_dir(plants_config.get('workdir', None), create=True)
        if not plants_config['workdir']:
            self.log.error('No valid work directory defined')
            return {}
        
        docking = PlantsDocking(**plants_config)
        docking.run(protein, ligand)
        results = docking.results()
        
        self.log.info('Finished docking. method: {method}', method='plants', **self.session_config)
            
        return {'result': results, 'dir': plants_config['workdir']}

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
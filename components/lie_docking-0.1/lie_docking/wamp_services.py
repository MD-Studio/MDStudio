# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import time
import random

from autobahn.wamp.types import RegisterOptions
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from twisted.logger import Logger
from twisted.internet.defer import inlineCallbacks

class DockingWampApi(ApplicationSession):

    """
    Docking WAMP methods.
    """
    
    logging = Logger()
   
    @inlineCallbacks
    def onJoin(self, details):
        
        self.logging.info("Init docking component", lie_user='mvdijk', lie_session=338776455, lie_namespace='docking')
        self._ident = "DockingWampApi (PID {}, Session {})".format(os.getpid(), details.session)
        yield self.register(self.docking_run, u'liestudio.docking.run', options=RegisterOptions(invoke=u'roundrobin'))
        self.logging.info("DockingWampApi: docking_run() registered!")
    
    def onLeave(self, details):
        
        self.logging.info("exit docking component", lie_user='mvdijk', lie_session=338776455, lie_namespace='docking')
    
    def docking_run(self, protein, ligand, method='plants'):
        """
        Perform a docking run using one of the available methods
        
        :param protein: protein 3D structure file
        :type protein:  str
        :param ligand:  ligand 3D structure file
        :type ligand:   str
        :param method:  docking method to use
        :type method:   str
        """
        
        self.logging.info('Initiate docking. method: {0}'.format(method),
            lie_user='mvdijk', lie_session=338776455, lie_namespace='docking')
        
        if method == "plants":
            from plants_docking import PlantsDocking
            
            workdir = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/docking_{0}'.format(random.randint(1,1000))
            _exec = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/components/lie_docking-0.1/lie_docking/bin/plants_darwin'
            docking = PlantsDocking(workdir, exec_path=_exec)
            docking['bindingsite_center'] = [7.79934,9.49666,3.39229]
            docking.run(protein, ligand)
            results = docking.results()
        
        self.logging.info("Finished docking", lie_user='mvdijk', lie_session=338776455, lie_namespace='docking')
        return {'result': results}

def make(config):
    ##
    # This component factory creates instances of the
    # application component to run.
    ##
    # The function will get called either during development
    # using the ApplicationRunner below, or as  a plugin running
    # hosted in a WAMPlet container such as a Crossbar.io worker.
    ##
    if config:
        return DockingWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'Awesome WAMPlet 1',
                'description': 'This is just a test WAMPlet that provides some procedures to call.'}

if __name__ == '__main__':
    
    # test drive the component during development ..
    runner = ApplicationRunner(
        url="wss://localhost:8083/ws",
        realm="liestudio")  # app-level debugging

    runner.run(make)
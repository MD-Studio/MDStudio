# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import time

from autobahn import wamp
from autobahn.wamp.types import RegisterOptions
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from twisted.logger import Logger
from twisted.internet.defer import inlineCallbacks

class StructuresWampApi(ApplicationSession):

    """
    Structure database WAMP methods.
    """
    
    logging = Logger()
   
    @inlineCallbacks
    def onJoin(self, details):
        self._ident = "StructureWampApi (PID {}, Session {})".format(os.getpid(), details.session)
        yield self.register(self.get_structure, u'liestudio.structures.get_structure', options=RegisterOptions(invoke=u'roundrobin'))
        self.logging.info("DockingWampApi: get_structure() registered!")
    
    def get_structure(self, structure):
        
        self.logging.info("Return structure: {0}".format(structure),
            lie_user='mvdijk', lie_session=338776455, lie_namespace='structures')
        
        return {'result': structure}

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
        return StructuresWampApi(config)
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
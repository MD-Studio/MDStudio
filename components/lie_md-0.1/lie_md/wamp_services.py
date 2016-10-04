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

class MDWampApi(ApplicationSession):

    """
    Docking WAMP methods.
    """
    
    logging = Logger()
   
    @inlineCallbacks
    def onJoin(self, details):
        self._ident = "MDWampApi (PID {}, Session {})".format(os.getpid(), details.session)
        yield self.register(self.md_run, u'liestudio.md.run', options=RegisterOptions(invoke=u'roundrobin'))
        self.logging.info("MDWampApi: md_run() registered!")
    
    def md_run(self, structure):
        
        sl = 2
        self.logging.info("Running md for structure {0} Simulate by sleep for {1} sec.".format(structure, sl),
            lie_user='mvdijk', lie_session=338776455, lie_namespace='md')
        time.sleep(sl)
        self.logging.info("Finished MD", lie_user='mvdijk', lie_session=338776455, lie_namespace='md')
        
        return {'result': '{0}_md'.format(structure)}

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
        return MDWampApi(config)
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
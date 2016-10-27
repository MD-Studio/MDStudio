# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import time
import random

from   autobahn import wamp
from   autobahn.wamp.types import RegisterOptions
from   twisted.internet.defer import inlineCallbacks

from   lie_system  import LieApplicationSession

class MDWampApi(LieApplicationSession):

    """
    MD WAMP methods.
    """
    
    @inlineCallbacks
    def onJoin(self, details):
        self._ident = "MDWampApi (PID {}, Session {})".format(os.getpid(), details.session)
        yield self.register(self.md_run, u'liestudio.md.run', options=RegisterOptions(invoke=u'roundrobin'))
        self.logging.info("MDWampApi: md_run() registered!")
    
    def md_run(self, structure):
        
        sl = random.randint(10,200)
        self.logging.info("Running md for structure. Simulate by sleep for {0} sec.".format(sl),
            lie_user='mvdijk', lie_session=338776455, lie_namespace='md')
        time.sleep(sl)
        self.logging.info("Finished MD", lie_user='mvdijk', lie_session=338776455, lie_namespace='md')
        
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
        return MDWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'Awesome WAMPlet 1',
                'description': 'This is just a test WAMPlet that provides some procedures to call.'}
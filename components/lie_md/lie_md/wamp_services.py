# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import sys
import random

from autobahn import wamp
from autobahn.wamp.types import RegisterOptions
from autobahn.twisted.util import sleep
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from autobahn.twisted.util import sleep

from mdstudio.application_session import BaseApplicationSession
from mdstudio.runner import main
from mdstudio.token_application_session import TokenApplicationSession


class MDWampApi(BaseApplicationSession):

    """
    MD WAMP methods.
    """
    jobid = 0

    @wamp.register(u'liegroup.md.status', options=RegisterOptions(invoke=u'roundrobin'))
    def md_status(self):
        
        return 'running job: {0}'.format(self.jobid)

    @wamp.register(u'liegroup.md.run', options=RegisterOptions(invoke=u'roundrobin'))
    @inlineCallbacks
    def md_run(self, structure):

        sl = random.randint(10, 200)
        self.jobid = sl
        self.log.info("Running md for structure. Simulate by sleep for {0} sec.".format(sl),
                      lie_user='mvdijk', lie_session=338776455, lie_namespace='md')
        yield sleep(sl)
        self.log.info("Finished MD", lie_user='mvdijk', lie_session=338776455, lie_namespace='md')

        returnValue({'result': structure})
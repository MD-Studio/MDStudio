# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import random

from autobahn import wamp
from autobahn.twisted.util import sleep
from autobahn.wamp.types import RegisterOptions
from twisted.internet.defer import inlineCallbacks, returnValue

from mdstudio.component.session import ComponentSession


class MDWampApi(ComponentSession):

    """
    MD WAMP methods.
    """
    jobid = 0

    def pre_init(self):
        self.component_config.static.vendor = 'mdgroup'
        self.component_config.static.component = 'md'

    @wamp.register(u'mdgroup.md.endpoint.status', options=RegisterOptions(invoke=u'roundrobin'))
    def md_status(self):
        
        return 'running job: {0}'.format(self.jobid)

    @wamp.register(u'mdgroup.md.endpoint.run', options=RegisterOptions(invoke=u'roundrobin'))
    @inlineCallbacks
    def md_run(self, structure):

        sl = random.randint(10, 200)
        self.jobid = sl
        self.log.info("Running md for structure. Simulate by sleep for {0} sec.".format(sl),
                      lie_user='mvdijk', lie_session=338776455, lie_namespace='md')
        yield sleep(sl)
        self.log.info("Finished MD", lie_user='mvdijk', lie_session=338776455, lie_namespace='md')

        returnValue({'result': structure})
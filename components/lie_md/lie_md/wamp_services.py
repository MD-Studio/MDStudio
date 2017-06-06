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
from twisted.internet.defer import inlineCallbacks, returnValue

from lie_system import LieApplicationSession


class MDWampApi(LieApplicationSession):

    """
    MD WAMP methods.
    """
    jobid = 0

    @inlineCallbacks
    def onRun(self, details):

        yield self.register(self.md_run, u'liestudio.md.run', options=RegisterOptions(invoke=u'roundrobin'))
        yield self.register(self.md_status, u'liestudio.md.status', options=RegisterOptions(invoke=u'roundrobin'))
        self.log.info("MDWampApi: md_run() registered!")

    def md_status(self):

        return 'running job: {0}'.format(self.jobid)

    @inlineCallbacks
    def md_run(self, structure):

        sl = random.randint(10, 200)
        self.jobid = sl
        self.log.info("Running md for structure. Simulate by sleep for {0} sec.".format(sl),
                      lie_user='mvdijk', lie_session=338776455, lie_namespace='md')
        yield sleep(sl)
        self.log.info("Finished MD", lie_user='mvdijk', lie_session=338776455, lie_namespace='md')

        returnValue({'result': structure})


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
        return MDWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio Molecular Dynamics WAMPlet',
                'description': 'WAMPlet proving LIEStudio molecular dynamics endpoints'}

# -*- coding: utf-8 -*-

"""
Unit tests for the config component WAMP API
"""

import os, sys
import shutil

# Add modules in package to path so we can import them
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from   autobahn.twisted.util    import sleep
from   autobahn.twisted         import wamp
from   twisted.trial            import unittest
from   twisted.internet         import defer
from   twisted.application      import service

from   lie_config.wamp_services import ConfigWampApi

class CaseComponent(wamp.ApplicationSession):
    """
    Application code goes here. This is an example component that calls
    a remote procedure on a WAMP peer, subscribes to a topic to receive
    events, and then stops the world after some events.
    """

    def __init__(self, config):
        wamp.ApplicationSession.__init__(self, config)
        self.test = config.extra['test']
        self.stop = False
        self.finished = False

    def log(self, message, testpass=True):
        
        test_pass_message = 'error'
        if testpass:
            test_pass_message = 'ok'
        
        msg = u'test ({0}) {1} ... {2}'.format(self.__class__.__name__, message, test_pass_message)
        print(msg)

    def finish(self):
        if not self.finished:
            self.test.deferred.callback(None)
            self.finished = True
        else:
            print("already finished")

class GetConfig(CaseComponent):
    """
    Autobahn WAMP ApplicationSession testing configuration handling
    """
    
    @defer.inlineCallbacks
    def onJoin(self, details):
        
        # Test correct test user login
        res = yield self.call(u'liestudio.config.get', 'lie_logging')
        testpass = type(res) == dict
        self.log("logging config: {0}".format(res), testpass=testpass)
        
        self.finish()

class ConfigWAMPTests(unittest.TestCase):
    
    def setUp(self):
        self.url = 'ws://localhost:8080/ws'
        self.realm = u"wamp_test"

    @defer.inlineCallbacks
    def runOneTest(self, components):
        self.deferred = defer.Deferred()
        app = service.MultiService()
        for component in components:
            c = wamp.Service(
                url=self.url,
                extra=dict(test=self),
                realm=self.realm,
                make=component,
            )
            c.setServiceParent(app)

        app.startService()
        yield self.deferred
        app.stopService()

    @defer.inlineCallbacks
    def test_case1(self):
        
       yield self.runOneTest([GetConfig])

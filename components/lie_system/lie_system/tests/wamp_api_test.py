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

class WAMPUnitTestBase(wamp.ApplicationSession):
    """
    Base class for WAMP API unit tests
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


class GetSingleConfig(WAMPUnitTestBase):
    """
    Autobahn WAMP ApplicationSession test session.
    
    Test retrieval of configuration based on a single configuration key.
    """
    
    @defer.inlineCallbacks
    def onJoin(self, details):
        
        res = yield self.call(u'liestudio.config.get', 'lie_logging')
        
        returndict = type(res) == dict
        returnsingle = len(res) == 1 and 'lie_logging' in res
        
        self.log("logging config: {0}".format(res), testpass=all([returndict, returnsingle]))
        self.finish()


class GetMultipleConfig(WAMPUnitTestBase):
    """
    Autobahn WAMP ApplicationSession test session.
    
    Test retrieval of configuration based on multiple configuration keys.
    """
    
    @defer.inlineCallbacks
    def onJoin(self, details):
        
        res = yield self.call(u'liestudio.config.get', ['lie_logging','system'])
        
        returndict = type(res) == dict
        returnmult = len(res) == 2 and set(res.keys()) == set([u'system', u'lie_logging'])
        
        self.log("logging config: {0}".format(res), testpass=all([returndict, returnmult]))
        self.finish()


class GetNonexistingConfig(WAMPUnitTestBase):
    """
    Autobahn WAMP ApplicationSession test session.
    
    Test retrieval of non-existing configuration key.
    """
    
    @defer.inlineCallbacks
    def onJoin(self, details):
        
        res = yield self.call(u'liestudio.config.get', 'notexisting')
        
        returndict = type(res) == dict
        returnempty = len(res) == 0
        
        self.log("logging config: {0}".format(res), testpass=all([returndict, returnempty]))
        self.finish()
        

class ConfigWAMPTests(unittest.TestCase):
    """
    Run lie_config module WAMP API tests using a Crossbar test router
    """
    
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
    def test_get_single(self):
        
       yield self.runOneTest([GetSingleConfig])
    
    @defer.inlineCallbacks
    def test_get_multiple(self):
        
       yield self.runOneTest([GetMultipleConfig])
    
    @defer.inlineCallbacks
    def test_get_nonexisting(self):
        
       yield self.runOneTest([GetNonexistingConfig])

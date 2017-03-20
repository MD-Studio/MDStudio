# -*- coding: utf-8 -*-

"""
Unit tests for the user component WAMP API
"""

import os, sys
import shutil

# Add modules in package to path so we can import them
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from   autobahn.twisted       import wamp
from   twisted.trial          import unittest
from   twisted.internet       import defer
from   twisted.application    import service

# Test import of the lie_db database drivers
# If unable to import we cannot run the UserWAMPTests
# The twisted unittest does not have the @unittest.skipIf decorator
dbenabled = False
try:
  from lie_db import BootstrapMongoDB
  dbenabled = True
except:
  pass

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

class UserAuthentication(CaseComponent):
    """
    Autobahn WAMP ApplicationSession testing user authentication
    """
    
    @defer.inlineCallbacks
    def onJoin(self, details):
        
        # Test correct test user login
        res = yield self.call(u'liestudio.user.login', 'test1', 'test1')
        testpass = type(res) == dict
        self.log("correct login: {0}".format(res), testpass=testpass)
    
        # Test incorrect user logn
        res = yield self.call(u'liestudio.user.login', 'dummy', 'user')
        testpass = res == False
        self.log("incorrect login: {0}".format(res), testpass=testpass)
        
        self.finish()

class UserWAMPTests(unittest.TestCase):
    
    _mongodb_database_name = 'unittest_db'
    _currpath = os.path.abspath(__file__)
    _dbpath = os.path.join(os.path.dirname(_currpath), _mongodb_database_name)
    _dblog = os.path.join(os.path.dirname(_currpath), '{0}.log'.format(_mongodb_database_name))
    
    @classmethod
    def setUpClass(cls):
        """
        UserWAMPTests class setup
        
        Test for database connection
        """
        
        if not dbenabled:
            print('Unable to run UserWAMPTests: mongodb not enabled')
        
    @classmethod
    def tearDownClass(cls):
        """
        UserWAMPTests class teardown

        * Disconnect from MongoDB
        * Stop mongod process
        * Remove MongoDB test database and logfiles created in 
          UserDatabaseTests class
        """
        
        if dbenabled:
            # Stop the database
            cls.db = BootstrapMongoDB(dbpath=cls._dbpath,
                                      dbname='liestudio',
                                      dblog=cls._dblog)
            cls.db.stop(terminate_mongod_on_exit=True)

            if os.path.exists(cls._dbpath):
                shutil.rmtree(cls._dbpath)
            if os.path.exists(cls._dblog):
                os.remove(cls._dblog)

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
        
        if dbenabled:
            yield self.runOneTest([UserAuthentication])

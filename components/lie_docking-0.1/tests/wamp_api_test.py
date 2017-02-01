# -*- coding: utf-8 -*-

"""
Unit tests for the docking component WAMP API
"""

import os
import sys
import shutil

# Add modules in package to path so we can import them
__rootpath__ = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(__rootpath__, '..')))

from   autobahn.twisted.util    import sleep
from   autobahn.twisted         import wamp
from   twisted.trial            import unittest
from   twisted.internet         import defer
from   twisted.application      import service

protein=None
with open(os.path.join(__rootpath__, 'protein.mol2'), 'r') as pfile:
    protein = pfile.read()

ligand=None
with open(os.path.join(__rootpath__, 'ligand.mol2'), 'r') as lfile:
    ligand = lfile.read()

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


class RunPlantsDocking(WAMPUnitTestBase):
    """
    Autobahn WAMP ApplicationSession test session.
    
    Test lie_docking PLANTS based docking run
    """
    
    @defer.inlineCallbacks
    def onJoin(self, details):
        
        config = {'bindingsite_center': [7.79934,9.49666,3.39229],
                  'workdir': __rootpath__,
                  'exec_path': os.path.join(__rootpath__, '../../../bin/plants_darwin')}
        res = yield self.call(u'liestudio.docking.plants', protein, ligand, config=config)
        
        means = [k for k,v in res.get('result', {}).items() if v['mean']]
        returndict = type(res) == dict and res.get('result', None) != None
        
        self.log('Number of docking poses: {0}'.format(len(res['result'])), testpass=returndict)
        
        structures_retrieved = []
        for s in means:
            structure = yield self.call(u'liestudio.docking.get', os.path.join(res['dir'], s))
            structures_retrieved.append(structure.get('result',None) != None)

        self.log('Retrieved {0} docked structures representing cluster means'.format(len(structures_retrieved)), testpass=all(structures_retrieved))
    
        # Remove docking directory
        if os.path.exists(res.get('dir', None)):
            shutil.rmtree(res.get('dir'))
        
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
    def test_plants_docking(self):
        
       yield self.runOneTest([RunPlantsDocking])
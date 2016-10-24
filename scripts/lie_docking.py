import sys

from   autobahn.twisted.wamp  import ApplicationRunner
from   twisted.internet.defer import inlineCallbacks, returnValue
from   twisted.internet       import reactor

from   lie_system             import LieApplicationSession

class LIEWorkflow(LieApplicationSession):
    
    _isauthenticated = False
    
    @inlineCallbacks
    def authenticate(self, username, password):
        
        authentication = yield self.call(u'liestudio.user.login', username, password)
        if authentication:
            self._isauthenticated = True
        self.logging.info('Authentication of user: {0}, {1}'.format(username, self._isauthenticated))
        
        returnValue(self._isauthenticated)
        
    @inlineCallbacks
    def onJoin(self, details):
        
        self.logging.info("Simulating a LIE workflow")
        print(self.config)
        
        #Try to login
        # print(yield self.authenticate('lieadmin','liepw@#'))
        # reactor.stop()
        # return
        #
        # if not isauthenticated:
        #   raise('Unable to authenticate')
          
        #Get a number of ligand structures
        lig_cids = ['cid001', 'cid002', 'cid003', 'cid004', 'cid005']      
        self.logging.info('Retrieve structures by cid for {0} compounds'.format(len(lig_cids)))
        protein  = yield self.call(u'liestudio.structures.get_structure', 'protein')
        ligands  = [self.call(u'liestudio.structures.get_structure', cid) for cid in lig_cids]
        
        #Dock structures
        self.logging.info('Dock {0} structures'.format(len(ligands)))
        docked = []
        for structure in ligands:
          b = yield structure
          docked.append(self.call(u'liestudio.docking.run', protein['result'], b['result']))
        
        #Simulating a MD run
        self.logging.info('Running MD for {0} structures'.format(len(docked)))
        md = []
        for result in docked:
          k = yield result
          md.append(self.call(u'liestudio.md.run', k['result']))
        
        for n in md:
          f = yield(n)
          print(f)
        
        self.logging.info('Finished workflow')
        reactor.stop()

if __name__ == '__main__':
   
    runner = ApplicationRunner(
        u"ws://localhost:8080/ws",
        u"liestudio",
    )
    runner.run(LIEWorkflow)
    
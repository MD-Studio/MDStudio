import sys
import os

from   OpenSSL                     import crypto
from   autobahn.twisted.wamp       import ApplicationRunner
from   twisted.internet.defer      import inlineCallbacks, returnValue
from   twisted.internet            import reactor
from   twisted.internet._sslverify import OpenSSLCertificateAuthorities
from   twisted.internet.ssl        import CertificateOptions

from   lie_system                  import LieApplicationSession

class LIEWorkflow(LieApplicationSession):
    
    @inlineCallbacks
    def onRun(self, details):
        
        self.log.info("Simulating a LIE workflow")
        
        #Get a number of ligand structures
        lig_cids = ['cid001', 'cid002', 'cid003', 'cid004', 'cid005']      
        self.log.info('Retrieve structures by cid for {0} compounds'.format(len(lig_cids)))
        protein  = yield self.call(u'liestudio.structures.get_structure', 'protein')
        ligands  = [self.call(u'liestudio.structures.get_structure', cid) for cid in lig_cids]
        
        #Dock structures
        self.log.info('Dock {0} structures'.format(len(ligands)))
        docking_config = {'workdir':'/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/tmp',
                          'bindingsite_center': [7.79934,9.49666,3.39229]}
        docked = []
        for ligand in ligands:
          lig = yield ligand
          docked.append(self.call(u'liestudio.docking.plants', protein['result'], lig['result'], config=docking_config))
        
        #Simulating a MD run
        self.log.info('Running MD for {0} structures'.format(len(docked)))
        md = []
        for result in docked:
          k = yield result
          md.append(self.call(u'liestudio.md.run', k['result']))
        
        for n in md:
          f = yield(n)
          print(f)
        
        self.log.info('Finished workflow')
        reactor.stop()
        return

if __name__ == '__main__':
    
    # load the self-signed cert the server is using
    certpath = os.path.join(os.path.dirname(__file__), '../data/crossbar/server_cert.pem')
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(certpath, 'r').read())
    
    # tell Twisted to use just the one certificate we loaded to verify connections
    options = CertificateOptions(trustRoot=OpenSSLCertificateAuthorities([cert]))
        
    runner = ApplicationRunner(
        u"wss://localhost:8080/ws",
        u"liestudio",
        extra={'authid':u'lieadmin', 'password':u'liepw@#', 'auth_method':u'ticket'},
        ssl=options
    )
    runner.run(LIEWorkflow, auto_reconnect=True)
    
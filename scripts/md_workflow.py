import sys
import os

from   OpenSSL                     import crypto
from   autobahn.twisted.wamp       import ApplicationRunner
from   twisted.internet.defer      import inlineCallbacks, returnValue
from   twisted.internet            import reactor
from   twisted.internet._sslverify import OpenSSLCertificateAuthorities
from   twisted.internet.ssl        import CertificateOptions

from   lie_system                  import LieApplicationSession
from   lie_topology                import TopologyWampApi

class MdWorkflow(LieApplicationSession):
    
    @inlineCallbacks
    def onRun(self, details):
        
        self.log.info("Simulating a MD workflow")
        
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
        #u"wss://localhost:8080/ws",
        u"ws://localhost:8080/ws",
        u"liestudio",
        extra={'authid':u'lieadmin', 'password':u'liepw@#', 'auth_method':u'ticket'},
        #ssl=options
    );
    
    runner.run(TopologyWampApi, auto_reconnect=True )
    #runner.run(MdWorkflow, auto_reconnect=True)
    
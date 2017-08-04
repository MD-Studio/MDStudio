import os

from autobahn.twisted.wamp  import ApplicationRunner, ComponentConfig
from twisted.internet.ssl   import CertificateOptions
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor
from twisted.logger import Logger
import OpenSSL

crossbar_host = os.getenv('CROSSBAR_HOST', 'localhost')
print('Crossbar host is: {}'.format(crossbar_host))

cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, open('data/crossbar/server_cert.pem').read())
options = CertificateOptions(caCerts=[cert])

runner = ApplicationRunner(
    u"wss://{}:8080/ws".format(crossbar_host),
    u"mdstudio",
    ssl=options
)

def main(component, extra=None, oninit=None, onexit=None, auto_reconnect=True, start_reactor=True):
    def make(cfg):
        if extra:
            cfg.extra.update(extra)

        if callable(component):
            return component(cfg)
        else:
            return component
    

    return runner.run(make, auto_reconnect=auto_reconnect, start_reactor=(not reactor.running and start_reactor))

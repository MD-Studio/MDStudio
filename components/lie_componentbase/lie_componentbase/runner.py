import os

from autobahn.twisted.wamp  import ApplicationRunner
from twisted.internet.ssl   import CertificateOptions
import OpenSSL

def main(component, extra=None, oninit=None, onexit=None):
    if oninit:
        oninit()

    crossbar_host = os.getenv('CROSSBAR_HOST', 'localhost')
    print('Crossbar host is: {}'.format(crossbar_host))

    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, open('data/crossbar/server_cert.pem').read())
    options = CertificateOptions(caCerts=[cert])

    runner = ApplicationRunner(
        u"wss://{}:8080/ws".format(crossbar_host),
        u"liestudio",
        ssl=options,
        extra=extra
    )

    runner.run(component, auto_reconnect=True)


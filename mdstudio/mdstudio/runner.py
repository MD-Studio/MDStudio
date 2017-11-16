# coding=utf-8
import OpenSSL
import os
from autobahn.twisted.wamp import ApplicationRunner
from mdstudio.component.impl.common import CommonSession
from twisted.internet import reactor
from twisted.internet.ssl import CertificateOptions


def main(component, auto_reconnect=True):
    crossbar_host = os.getenv('CROSSBAR_HOST', 'localhost')
    print('Crossbar host is: {}'.format(crossbar_host))

    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, open('data/crossbar/server_cert.pem').read())
    options = CertificateOptions(caCerts=[cert])

    runner = ApplicationRunner(
        u"wss://{}:8080/ws".format(crossbar_host),
        u"mdstudio",
        ssl=options
    )

    def start_component(config):
        session = component(config) # type: CommonSession

        logdir = os.path.join(session.component_root_path, 'logs')
        if not os.path.isdir(logdir):
            os.mkdir(logdir)

        gitignorepath = os.path.join(logdir, '.gitignore')
        if not os.path.isfile(gitignorepath):
            with open(gitignorepath, 'w') as f:
                f.write('*')

    return runner.run(component, auto_reconnect=auto_reconnect, start_reactor=not reactor.running)

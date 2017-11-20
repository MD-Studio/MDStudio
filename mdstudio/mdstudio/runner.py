# coding=utf-8
from datetime import datetime

import OpenSSL
import os

import pytz
import twisted
from autobahn.twisted.wamp import ApplicationRunner
from twisted.python.logfile import DailyLogFile

from mdstudio.component.impl.common import CommonSession
from twisted.internet import reactor
from twisted.internet.ssl import CertificateOptions

from mdstudio.logging.impl.printing_observer import PrintingLogObserver


def main(component, auto_reconnect=True):
    crossbar_host = os.getenv('CROSSBAR_HOST', 'localhost')

    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, open('data/crossbar/server_cert.pem').read())
    options = CertificateOptions(caCerts=[cert])

    runner = ApplicationRunner(
        u"wss://{}:8080/ws".format(crossbar_host),
        u"mdstudio",
        ssl=options
    )

    def start_component(config):
        logdir = os.path.join(component.component_root_path(), 'logs')
        os.makedirs(logdir, exist_ok=True)

        gitignorepath = os.path.join(logdir, '.gitignore')
        if not os.path.isfile(gitignorepath):
            with open(gitignorepath, 'w') as f:
                f.write('*')

        log_file = DailyLogFile('daily.log', logdir)
        twisted.python.log.addObserver(PrintingLogObserver(log_file))

        ascii_brand = [
            r' __  __ ____      _             _ _',
            r'|  \/  |  _ \ ___| |_ _   _  __| (_) ___',
            r'| |\/| | | | / __| __| | | |/ _` | |/ _ \ ',
            r'| |  | | |_| \__ \ |_| |_| | (_| | | (_) |',
            r'|_|  |_|____/|___/\__|\__,_|\__,_|_|\___/''',
            ''
        ]

        for line in ascii_brand:
            print(line)

        print('Crossbar host is: {}'.format(crossbar_host))
        session = component(config)  # type: CommonSession
        return session

    try:
        runner.run(start_component, auto_reconnect=auto_reconnect, start_reactor=not reactor.running)
    finally:
        if reactor.running:
            reactor.stop()

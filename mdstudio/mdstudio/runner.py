# coding=utf-8

import os

import twisted
from autobahn.twisted.wamp import ApplicationRunner
from twisted.python.logfile import DailyLogFile

from mdstudio.component.impl.common import CommonSession
from twisted.internet import reactor, ssl
from twisted.internet.ssl import CertificateOptions

from mdstudio.logging.brand import ascii_brand
from mdstudio.logging.impl.printing_observer import PrintingLogObserver


def main(component, auto_reconnect=True, log_level='info', daily_log=True, extra=None):
    """
    :param component:       WAMP component to run
    :type component:        CommonSession
    :param auto_reconnect:  try automatic reconnect to WAMP broker
    :type auto_reconnect:   :py:bool
    :param log_level:       component specific log level for txaio logger as
                            none, critical, error, warn, info, debug, trace
    :type log_level:        :py:str
    :param daily_log:       store daily logs in the directory where the application
                            is launched ('logs' directory)
    :type daily_log:        :py:bool
    :param extra:           additional keyword arguments made available as part
                            of the component `config` argument.
    :type extra:            :py:dict
    """

    crossbar_host = os.getenv('CROSSBAR_HOST', 'localhost')

    with open(os.path.join(CommonSession.mdstudio_root_path(), '../data/crossbar/server_cert.pem'), 'r') as f:
        cert_data = f.read().encode('utf-8')

    cert = ssl.Certificate.loadPEM(cert_data)
    options = CertificateOptions(caCerts=[cert])
    extra = extra or {}
    extra['daily_log'] = daily_log

    print('Connecting to host: {}'.format(crossbar_host))

    runner = ApplicationRunner(
        u"wss://{}:8080/ws".format(crossbar_host),
        u"mdstudio",
        ssl=options,
        extra=extra
    )

    def start_component(config):

        # No logging if 'none'
        if log_level != 'none':

            if daily_log:
                logdir = os.path.join(component.component_root_path(), 'logs')
                if not os.path.exists(logdir):
                    os.makedirs(logdir)

                gitignorepath = os.path.join(logdir, '.gitignore')
                if not os.path.isfile(gitignorepath):
                    with open(gitignorepath, 'w') as f:
                        f.write('*')

                log_file = DailyLogFile('daily.log', logdir)
                twisted.python.log.addObserver(PrintingLogObserver(log_file))

            print(ascii_brand)
            print('Crossbar host is: {}'.format(crossbar_host))

        session = component(config)
        return session

    try:
        runner.run(start_component, auto_reconnect=auto_reconnect, start_reactor=not reactor.running, log_level=log_level)
    finally:
        if reactor.running:
            reactor.stop()

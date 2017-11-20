from collections import OrderedDict
from datetime import datetime
from tempfile import NamedTemporaryFile

import sys
import argparse

import copy

import pytz
import twisted
import yaml
import json
import os

from crossbar.controller.cli import run
from twisted.internet import reactor
from twisted.python.logfile import DailyLogFile

from mdstudio.logging.impl.printing_observer import PrintingLogObserver

if __name__ == '__main__':
    temp_config = None

    try:
        with open('crossbar_config.yml', 'r') as cc:
            config = yaml.load(cc)

        ring0_config = [{
            "type": "class",
            "classname": "lie_{role}.application.{component}Component".format(role=role, component=component),
            "realm": "mdstudio",
            "role": role
        } for role, component in {
            'auth': 'Auth',
            'db': 'DB',
            'schema': 'Schema',
            'logger': 'Logger'
        }.items()]

        wampcra_config = {
            "type": "static",
            "users": OrderedDict((role, {'role': role, 'secret': role}) for role in ['auth', 'db', 'schema', 'logger'])
        }

        parser = argparse.ArgumentParser(description='MDstudio application startup script')
        parser.add_argument('--dev', action='store_true', help='Flag to run in dev mode. Allows core components to start separately.')
        parser.add_argument('-s', '--skip-startup', nargs='+', metavar='COMPONENT', help='List of core components that are not started (--dev required)')
        args = parser.parse_args()

        if args.dev:
            if args.skip_startup:
                ring0_config = [v for v in ring0_config if v['role'] not in args.skip_startup]
            else:
                ring0_config = None

            config['workers'][0]['transports'][0]['paths']['ws']['auth'].update({'wampcra': wampcra_config})

        if ring0_config:
            config['workers'][0]['components'] = ring0_config

        temp_config = NamedTemporaryFile(delete=False, suffix='.json')
        temp_config.write(json.dumps(config).encode('utf-8'))
        temp_config.close()

        os.makedirs('logs', exist_ok=True)
        log_file = DailyLogFile('daily.log', 'logs')
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

        run('crossbar', [
            'start',
            '--cbdir',
            '.',
            '--config',
            temp_config.name,
            '--loglevel',
            'info',
        ], reactor=reactor)
    finally:
        if temp_config:
            os.remove(temp_config.name)

        if log_file:
            log_file.flush()
            log_file.close()

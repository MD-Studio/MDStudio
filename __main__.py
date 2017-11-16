from tempfile import NamedTemporaryFile

import sys
import argparse

import copy
import yaml
import json
import os

from crossbar.controller.cli import run

if __name__ == '__main__':
    temp_config = None

    try:
        with open('crossbar_config.yml', 'r') as cc:
            config = yaml.load(cc)

        ring0_config = [
            {
                "type": "class",
                "classname": "lie_auth.application.AuthComponent",
                "realm": "mdstudio",
                "role": "auth"
            },
            {
                "type": "class",
                "classname": "lie_db.application.DBComponent",
                "realm": "mdstudio",
                "role": "db"
            },
            {
                "type": "class",
                "classname": "lie_schema.application.SchemaComponent",
                "realm": "mdstudio",
                "role": "schema"
            },
            {
                "type": "class",
                "classname": "lie_logger.application.LoggerComponent",
                "realm": "mdstudio",
                "role": "logger"
            }
        ]

        wampcra_config = {
            "type": "static",
            "users": {
                "db": {
                    "role": "db",
                    "secret": "db"
                },
                "auth": {
                    "role": "auth",
                    "secret": "auth"
                },
                "schema": {
                    "role": "schema",
                    "secret": "schema"
                },
                "logger": {
                    "role": "logger",
                    "secret": "logger"
                }
            }
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

        run('crossbar', [
            'start',
            '--cbdir',
            '.',
            '--config',
            temp_config.name,
            '--logdir',
            './data/logs',
            '--loglevel',
            'info'
        ])
    finally:
        if temp_config:
            os.remove(temp_config.name)

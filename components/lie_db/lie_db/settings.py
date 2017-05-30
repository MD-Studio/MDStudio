# -*- coding: utf-8 -*-

"""
file: settings.py

db module wide settings
"""
import os

path = os.path.dirname(os.path.realpath(__file__))
mongoHost = os.getenv('MONGO_HOST', 'localhost')

SETTINGS = {
    'dbpath': '{}/data/liedb'.format(path),
    'dbname': 'liestudio',
    'dblog': '{}/data/logs/mongodb.log'.format(path),
    'port': 27017,
    'host': mongoHost,
    'create_db': True,
    'terminate_mongod_on_exit': False
}

APP_COLLECTION = {
    'application': None,
    'version': '1.0.0',
    'system': None,
    'user': None,
    'init_timestamp': None
}

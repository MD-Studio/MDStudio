# -*- coding: utf-8 -*-

"""
file: settings.py

db module wide settings
"""

SETTINGS = {
  'dbpath' : '/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/data/liedb',
  'dbname' : 'liestudio',
  'dblog'  : '/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/data/logs/mongodb.log',
  'port'   : 27017,
  'host'   : 'localhost',
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
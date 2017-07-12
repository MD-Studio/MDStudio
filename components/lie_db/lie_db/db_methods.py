# -*- coding: utf-8 -*-

"""
file: db_methods.py
"""

import os
import copy
import subprocess
import logging
import datetime
import getpass

from distutils import spawn
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from autobahn import wamp

from lie_componentbase import WampSchema, validate_json_schema

def get_host(settings):
    """
    Adds support to host switching needed for docker builds

    :param settings: the Settings object
    :return: The correct host
    """
    return os.getenv('_LIE_MONGO_HOST', settings.get('dbhost', 'localhost'))


def init_mongodb(session, settings):
    """
    Initiate the application MongoDB database
    """

    # Start the database
    db = BootstrapMongoDB(session=session,
                          dbpath=settings.get('dbpath'),
                          dbname=settings.get('dbname'),
                          dblog=settings.get('dblog'),
                          host=get_host(settings),
                          port=settings.get('dbport'))
    assert db.start()

    db = db.connect()
    appdata = db['{0}_data'.format(settings.get('dbname'))].find_one()
    logging.info('Initiate {application} database. Version: {version}, user: {user}'.format(**appdata))

    return db


def exit_mongodb(session, settings):
    """
    Clean termination of MongoDB
    """

    db = BootstrapMongoDB(session=session,
                          dbpath=settings.get('dbpath'),
                          dbname=settings.get('dbname'),
                          dblog=settings.get('dblog'),
                          host=get_host(settings),
                          port=settings.get('dbport'))
    db.stop(terminate_mongod_on_exit=settings.get('terminate_mongod_on_exit', False))


def mongodb_connect(host=get_host({}), port=27017, **kwargs):
    """
    Connect to a running MongoDB database

    :param host: URL of the database
    :param port: port number
    :type port:  int
    """

    # A port number is sometimes defined as a python long (L) by for instances
    # databases or serializers. The MongoClient class does not exept this.
    port = int(port)

    client = MongoClient(host=host, port=port, **kwargs)
    return client


class BootstrapMongoDB(object):
    """
    Establish connection to the application MongoDB database.

    The bootstrap process involves:
    * Start a local instance if the MongoDB mongod process or
    * Connecting to a remote MongoDB server
    * Check for a valid application database and create on if needed.

    TODO: Add database authentication
    """

    def __init__(self, session, dbpath, dbname='liedb', mongod_path=None, host=None, port=27017, dblog=None):

        if dbpath:
            self._dbpath = os.path.abspath(dbpath)

        self._session = session
        self._dbname = dbname
        self._mongod_path = mongod_path
        self._host = host
        self._port = port
        self._dblog = dblog
        self._create_db = True
        self._app_collection_template = WampSchema('db', 'app_collection', 1)

        self.did_create_local_db = False
        self.db = None

    @property
    def mongod_path(self):
        """
        Resolve the local MongoDB mongod executable path.

        :return: mongod path or None
        :rtype:  string or None
        """

        path = self._mongod_path
        if path:
            path = os.path.abspath(path)
            if not (os.path.exists(path) and os.access(path, os.X_OK)):
                logging.error('No (exacutable) mongod at: {0}'.format(path))
                path = None

        # Check if 'mongod' executable in path
        if not path:

            path = spawn.find_executable('mongod')
            if not path:
                logging.error('Unable to find mongod executable in environment')

        self._mongod_path = path
        return path

    @property
    def has_database(self):

        return self._dbname in self.db.database_names()

    @property
    def info(self):
        """
        Return MongoDB server information

        :rtype: :py:class:`dict`
        """

        if self.isrunning:
            client = MongoClient(host=self._host, port=self._port, connect=False,
                                 connectTimeoutMS=2000,
                                 serverSelectionTimeoutMS=2000)
            return client.server_info()
        else:
            logging.warning('Unable to connect to MongoDB at: {0}:{1}'.format(self._host, self._port))

        return {}

    @property
    def isrunning(self):
        """
        Check for a running MongoDB server
        """

        # Init Mongo Client without immediately connecting. Set connect- and
        # server Selection timeout to 2 sec. for fast connection probing.
        client = mongodb_connect(host=self._host,
                                 port=self._port,
                                 connect=False,
                                 connectTimeoutMS=2000,
                                 serverSelectionTimeoutMS=2000)

        # Try to establish connection
        try:
            client.admin.command("ismaster")
        except ConnectionFailure:
            return False

        return True

    @property
    def isremote(self):
        """
        Check if the database address to connect to is local or remote

        :return: true of false for remote or local database respectively
        :rtype: bool
        """

        if 'localhost' in self._host or '127.0.0.1' in self._host:
            return False
        return True

    @property
    def pid(self):
        """
        Get the process identifier (pid) of a running mongod process

        :return: mongod pid
        :rtype: int
        """

        pid = None
        try:
            pid = subprocess.check_output(['pgrep', os.path.basename(self.mongod_path)])
        except subprocess.CalledProcessError or OSError:
            pass

        if pid:
            pid = pid.strip()
            if pid.isdigit():
                pid = int(pid)

        return pid

    def _start_mongodb(self):
        """
        Start a local mongod process
        """

        cmd = [self.mongod_path, '--fork',
               '--dbpath', self._dbpath,
               '--port', str(self._port),
               '--logpath', self._dblog,
               '--bind_ip', '127.0.0.1']

        subprocess.Popen(cmd, stdout=subprocess.PIPE)

        return self.isrunning

    def _add_app_collection(self):
        """
        Add application collection to the database from template
        """

        # Make a new database with application name
        liedb = self.db[self._dbname]

        # Make a new collection with primary app data
        liedb_data = liedb['{0}_data'.format(self._dbname)]

        # Add primary app data from template
        appdata = {
            'application': self._dbname,
            'init_timestamp': datetime.datetime.utcnow()
        }

        try:
            appdata['user'] = getpass.getuser()
        except Exception as e:
            appdata['user'] = 'docker'

        validate_json_schema(self._session, self._app_collection_template, appdata)
        liedb_data.insert_one(appdata)

    def connect(self):
        """
        Connect to a MongoDB server.

        :return: PyMongo MongoClient instance
        """

        # Init pymongo MongoClient instance
        if not self.db:
            self.db = mongodb_connect(host=self._host, port=self._port)

        # Check for appdatabase collection
        if not self.has_database:
            if self.did_create_local_db:
                self._add_app_collection()
                logging.info('Create {0} application data collection'.format(self._dbname))
            elif self._create_db:
                self._add_app_collection()
                logging.warning('Create {0} application data collection'.format(self._dbname))
            else:
                raise Exception('Unable to create application data collection')

        return self.db[self._dbname]

    def start(self):
        """
        Start a local MongodDB server.

        Start a local mongod process if:
        * MongoDB is not already running
        * We are not connecting to a remote database
        * A mongod executable was found
        """

        # Check if mongod is already running
        if self.isrunning:
            logging.info('MongoDB already running')
            return True

        # Check if we need to connect to a local or remote database
        if self.isremote:
            logging.info('Connect to remote database. Not starting local database')
            return True

        # Check if MongoDB is installed
        assert self.mongod_path

        # Database path needs to exists before start.
        if not os.path.exists(self._dbpath):
            os.makedirs(self._dbpath)
            logging.info('Create new MongoDB at: {0}'.format(self._dbpath))

        # Start mongod
        if self._start_mongodb():
            logging.info("Launch MongoDB server, mongod process with pid: {0}".format(self.pid))
            logging.info("Set database path to: {0}".format(self._dbpath))
            self.did_create_local_db = True
            return True
        else:
            logging.error('Unable to start MongoDB')
            return False

    def stop(self, terminate_mongod_on_exit=False):
        """
        Stop a local MongodDB server.

        Stop a local mongod proces if:
        * a MongoDB server is running
        * if it is not a remote server
        * if terminate_mongod_on_exit == True
        """

        # Check if mongod is running
        if not self.isrunning:
            logging.info('MongoDB not running')
            return True

        # Can't stop a remote database
        if self.isremote:
            logging.info('Using a remote database, unable to stop')
            return True

        # Close connections
        if self.db:
            self.db.close()
            logging.debug('Close active MongoDB connection')

        # Clean shutdown of mongod
        if terminate_mongod_on_exit:
            pid = self.pid
            if pid:
                process = subprocess.Popen(['kill', str(pid)], stdout=subprocess.PIPE)
                process.communicate()
                if process.returncode != 0:
                    logging.error('Unable to stop mongod instance with pid: {0}'.format(pid))
                    return False
            else:
                logging.error('Unable to obtain PID of running mongod instance')
                return False

            logging.info('Stopped mongod process')
        else:
            logging.info('Not stopping mongod process')

        return True

    def restart(self):
        """
        Restart a local MongoDB server
        """

        if self.stop():
            return self.start()
        return False

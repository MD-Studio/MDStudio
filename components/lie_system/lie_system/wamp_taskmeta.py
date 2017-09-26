# -*- coding: utf-8 -*-

"""
file: wamp_message_format.py
"""

import os
import time
import random
import json
import jsonpickle
import jsonschema

from getpass import getuser
from twisted.logger import Logger

# LieApplicationSession variables names defined in os.environ
ENVIRON = {'_LIE_WAMP_REALM': 'realm',
           '_LIE_AUTH_METHOD': 'authmethod',
           '_LIE_AUTH_USERNAME': 'username',
           '_LIE_AUTH_PASSWORD': 'password'}

logging = Logger()


def wamp_session_schema(
        path=os.path.join(os.path.dirname(__file__),
                          'wamp_session_schema.json')):
    """
    Return the JSON wamp session schema from file

    :param path: path to json schema file
    :type path:  :py:str
    """

    if os.path.isfile(path):
        wamp_session_schema = json.load(open(path))
        return wamp_session_schema
    else:
        logging.error('No such file {0}'.forma(path))
        return {}


def _schema_to_data(schema, data=None):

    default_data = {}

    required = schema.get('required', [])
    properties = schema.get('properties', {})

    for key, value in properties.items():
        if key in required:
            default_data[key] = value.get('default')

    # Update with existing data
    if data:
        default_data.update(data)

    return default_data


class WAMPTaskMetaData(object):
    """
    Class that handles initiation and updating of LIEStudio task metadata.

    The task metadata blueprint is handled by the `wamp_session_schema`
    JSON schema.
    """

    def __init__(self, metadata=None, **kwargs):

        # Init default task metadata
        self._session_schema = wamp_session_schema()
        self._metadata = _schema_to_data(self._session_schema, data=metadata)
        self.task_id()
        if not metadata:
            self._update_time(time_stamp='itime')

        # Update metadata with kwargs and environmental variables
        self.update(kwargs)
        self.update({
            (ENVIRON[k], os.environ[k]) for k in ENVIRON if k in os.environ})

        # Update defaults
        if 'system_user' not in self._metadata:
            self._metadata['system_user'] = getuser()
        if 'itime' not in self._metadata:
            self._metadata['itime'] = int(time.time())

        # Validate against schema
        self.validate()

        self._allowed_status_labels = self._session_schema['properties']['status']['enum']
        self._initialised = True

    def __call__(self):

        return self.dict()

    def __contains__(self, key):

        return key in self._metadata

    def __getattr__(self, attr):

        if attr in self._metadata:
            return self._metadata[attr]
        
        return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        propobj = getattr(self.__class__, attr, None)

        if '_initialised' not in self.__dict__:
            return dict.__setattr__(self, attr, value)
        elif isinstance(propobj, property) and propobj.fset:
            propobj.fset(self, value)
        elif attr in self._metadata:
            self.set(attr, value)
        else:
            self.__setitem__(attr, value)

    def __getitem__(self, item):

        if item in self._metadata:
            return self._metadata[item]

        return self.__dict__[item]

    def __setitem__(self, item, value):

        propobj = getattr(self.__class__, item, None)

        if isinstance(propobj, property) and propobj.fset:
            propobj.fset(self, value)
        elif item in self._metadata:
            self.set(item, value)
        else:
            self._metadata[item] = value

    @property
    def status(self):

        return self.get('status')

    @status.setter
    def status(self, value):

        value = value.lower()
        if value in self._allowed_status_labels:
            self._metadata['status'] = value
        else:
            raise LookupError(
                'Task status label "{0}" not allowed'.format(value))

    @property
    def authmethod(self):
        """
        Returns the Crossbar WAMP authentication method to use.
        A WAMP connection can possibly allow for multiple authentication
        methods.

        :rtype: list or None
        """

        authmethod = self.get('authmethod')
        if not authmethod:
            return None

        if hasattr(authmethod, '__iter__'):
            return [authmethod]

        return [authmethod]

    def task_id(self):

        if not self._metadata.get('task_id'):
            self._metadata['task_id'] = '{0}-{1}'.format(
                int(time.time()), random.randint(1000, 9999))

    def _update_time(self, time_stamp='utime'):

        if time_stamp != 'utime' and self._metadata.get(time_stamp):
            return

        self._metadata[time_stamp] = int(time.time())

    def set(self, key, value):

        self._metadata[key] = value
        self._update_time()

    def get(self, key, default=None):

        return self._metadata.get(key, default)

    def update(self, udict):

        self._metadata.update(udict)

    def serialize(self, unpicklable=False):

        return jsonpickle.encode(self.dict(), unpicklable=unpicklable)

    def dict(self):

        if 'password' in self._metadata:
            del self._metadata['password']

        return self._metadata

    def validate(self):

        jsonschema.validate(self._metadata, self._session_schema)

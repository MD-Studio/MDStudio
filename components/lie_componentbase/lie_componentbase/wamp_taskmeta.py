# -*- coding: utf-8 -*-

"""
file: wamp_message_format.py
"""

import os
import copy
import time
import random
import jsonpickle
import jsonschema

from getpass import getuser

from lie_componentbase.wamp_schema import liestudio_task_schema

class WAMPTaskMetaData(object):
    """
    Class that handles initiation and updating of LIEStudio task metadata.

    The task metadata blueprint is handled by the `liestudio_task_schema`
    JSON schema.
    """

    def __init__(self, metadata=None):

        # Init default task metadata
        self._metadata = {}
        self.task_id()
        if not metadata:
            self._update_time(time_stamp='itime')

        # Update defaults
        self._metadata['system_user'] = getuser()

        # Validate against schema
        self.validate()

        self._allowed_status_labels = liestudio_task_schema['properties']['status']['enum']
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

        if not '_initialised' in self.__dict__:
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
            raise LookupError('Task status label "{0}" not allowed'.format(value))

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
            self._metadata['task_id'] = '{0}-{1}'.format(int(time.time()), random.randint(1000, 9999))

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

        jsonschema.validate(self._metadata, liestudio_task_schema)
# -*- coding: utf-8 -*-

"""
file: wamp_message_format.py
"""

import os
import copy
import time
import random
import jsonpickle

from   getpass import getuser

envelope = {
    'realm': None,
    'package_name': None,
    'authid': None,
    'class_name': None,
    'authrole': 'default',
    'authmethod': None,
    'session': None,
    'status': None,
    'itime': None,
    'utime': None,
    'status_message': None,
    'task_id': None,
    'system_user': None,
    'app': 'liestudio'
}

ALLOWED_STATUS_LABELS = ('submitted', 'waiting', 'ready', 'scheduled', 'running',
                         'done', 'aborted', 'cancelled', 'cleared')

# LieApplicationSession variables names defined in os.environ
ENVIRON = {'_LIE_WAMP_REALM':'realm',
           '_LIE_AUTH_METHOD':'authmethod',
           '_LIE_AUTH_USERNAME':'username',
           '_LIE_AUTH_PASSWORD':'password'}

class WAMPMessageEnvelope(object):
    
    def __init__(self, envelope=envelope, **kwargs):
        
        self._envelope = copy.deepcopy(envelope)
        
        # Update envelope with kwargs and environmental variables
        self.update(kwargs)
        self.update(dict([(ENVIRON[k],os.environ[k]) for k in ENVIRON if k in os.environ]))
        
        # Update defaults
        self._set_task_id()
        self._update_time(time_stamp='itime')
        self._envelope['system_user'] = getuser()
        
        self._initialised = True
    
    def __call__(self):
        
        return self.dict()
    
    def __contains__(self, key):
        
        return key in self._envelope
        
    def __getattr__(self, attr):
        
        if attr in self._envelope:
            return self._envelope[attr]
        
        return object.__getattribute__(self, attr)
    
    def __setattr__(self, attr, value):
        propobj = getattr(self.__class__, attr, None)
        
        if not '_initialised' in self.__dict__:
            return dict.__setattr__(self, attr, value)
        elif isinstance(propobj, property) and propobj.fset:
            propobj.fset(self, value)
        elif attr in self._envelope:
            self.set(attr, value)
        else:
            self.__setitem__(attr, value)
    
    def __getitem__(self, item):
        
        if item in self._envelope:
            return self._envelope[item]
        
        return self.__dict__[item]
    
    def __setitem__(self, item, value):
        
        propobj = getattr(self.__class__, item, None)
        
        if isinstance(propobj, property) and propobj.fset:
            propobj.fset(self, value)
        elif item in self._envelope:
            self.set(item, value)
        else:
            self.__setitem__(item, value)
    
    @property
    def status(self):
        
        return self.get('status')
    
    @status.setter
    def status(self, value):
        
        value = value.lower()
        if value in ALLOWED_STATUS_LABELS:
            self._envelope['status'] = value
        else:
            raise LookupError, 'Task status label "{0}" not allowed'.format(value)
    
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
    
    def _set_task_id(self):
        
        if not self._envelope.get('task_id'):
            self._envelope['task_id'] = '{0}-{1}'.format(int(time.time()), random.randint(1000,9999))
    
    def _update_time(self, time_stamp='utime'):
        
        if time_stamp != 'utime' and self._envelope.get(time_stamp):
            return
        
        self._envelope[time_stamp] = int(time.time())
    
    def set(self, key, value):
        
        self._envelope[key] = value
        self._update_time()
    
    def get(self, key, default=None):
        
        return self._envelope.get(key, default)
    
    def update(self, udict):
        
        self._envelope.update(udict)
    
    def serialize(self, unpicklable=False):
        
        return jsonpickle.encode(self._envelope, unpicklable=unpicklable)
    
    def dict(self):
        
        return self._envelope
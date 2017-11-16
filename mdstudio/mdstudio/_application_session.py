# -*- coding: utf-8 -*-

import inspect
import itertools
import json
import os
import re

import time
import twisted
from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp import auth, cryptosign
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.logger import Logger
from twisted.python.failure import Failure
from twisted.python.logfile import DailyLogFile

from mdstudio.api.call_exception import CallException
from mdstudio.api.schema import Schema, validate_json_schema
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.logging import WampLogObserver, PrintingObserver
from mdstudio.util import resolve_config


class BaseApplicationSession(ApplicationSession):
    """
    BaseApplicationSession class

    Inherits from the Autobahn Twisted based `ApplicationSession 
    <http://autobahn.ws/python/reference/autobahn.twisted.html#autobahn.twisted.wamp.ApplicationSession>`_
    and extends it with methods to ease the process of automatic authentication,
    authorization and WAMP API configuration.

    It does so by overriding the five `placeholder methods <http://autobahn.ws/python/wamp/programming.html>`_
    that the ApplicationSession calls over the course of the session life cycle:

    * **onConnect**: first stage in establishing connection with the WAMP router
      (Crossbar). Define the rules of engagement; realm to join, authentication
      method to use.
    * **onChallenge**: authenticate using any of the Crossbar supported `methods <http://crossbar.io/docs/Authentication/>`_.
    * **onJoin**: register the API methods with the WAMP router and update local
      API configuration with settings retrieved by calling ``mdstudio.config.get``
    * **onLeave**: cleanup methods when leaving the realm
    * **onDisconnect**: cleanup methods when disconnecting from the WAMP router

    To enable custom events during the application life cycle, the
    BaseApplicationSession defines it's own placeholder methods. Do not override
    the five methods mentioned above but use these instead:

    * **onInit**: called at the end of the class constructor.
    * **onRun**: implement custom code to be called automatically when the WAMP
      session joins the realm. Called from the onJoin method.
    * **onExit**: cleanup methods called from the onLeave method.

    Logging: the Autobahn ApplicationSession initiates an instance of the
    Twisted logger as self.log
    """

    require_config = []

    def __init__(self, config=None, **kwargs):
        # replace default logger to support proper namespace
        self.log = Logger(namespace=self.component_info.get('namespace'))

        # Init toplevel ApplicationSession
        super(BaseApplicationSession, self).__init__(config)

        # start wamp logger for buffering
        f = None
        templogs = os.path.join(self._config_dir, 'wamplogs.temp')
        if os.path.isfile(templogs):
            f = open(templogs)
        self.wamp_logger = WampLogObserver(self, f, self.session_config.get('log_level', 'info'))
        if f:
            f.close()
            os.remove(templogs)
        twisted.python.log.addObserver(self.wamp_logger)

        # start file logger
        log_file = DailyLogFile('daily.log', package_logs_dir)
        self.file_logger = PrintingObserver(log_file, self.component_info.get('namespace'),
                                            self.session_config.get('log_level', 'info'))
        twisted.python.log.addObserver(self.file_logger)

        self.autolog = True
        self.autoschema = True

    @inlineCallbacks
    def onJoin(self, details):

        # Add self.disconnect to Event trigger in order to get propper shutdown
        # and exit of reactor event loop on Ctrl-C e.d.
        # reactor.addSystemEventTrigger('before', 'shutdown', self.leave)

        if self.autolog:
            self.wamp_logger.start_flushing()
        else:
            def logger_event(event):
                self.wamp_logger.start_flushing()
                self.logger_subscription.unsubscribe()
                self.logger_subscription = None

            self.log.info('Delayed logging for {package}', package=self.component_info['package_name'])
            self.logger_subscription = yield self.subscribe(logger_event, u'mdstudio.logger.endpoint.events.online')

        if self.autoschema:
            self._upload_schemas()
        else:
            def schema_event(event):
                self._upload_schemas()
                self.schema_subscription.unsubscribe()
                self.schema_subscription = None

            self.log.info('Delayed schema registration for {package}', package=self.component_info['package_name'])
            self.schema_subscription = yield self.subscribe(schema_event, u'mdstudio.schema.endpoint.events.online')

        self._register_scopes()

        reactor.addSystemEventTrigger('before', 'shutdown', self.onCleanup)

        # Call onRun hook.
        yield self.onRun(details)

    def onCleanup(self, *args, **kwargs):
        self.wamp_logger.stop_flushing()
        f = open(os.path.join(self._config_dir, 'wamplogs.temp'), 'w')
        self.wamp_logger.flush_remaining(f)
        f.close()

    @inlineCallbacks
    def onDisconnect(self):
        self.log.info('{class_name} of {package_name} disconnected from realm {realm}',
                      realm=self.session_config.get('realm'),
                      **self.component_info)

        self.wamp_logger.stop_flushing()

        res = yield super(BaseApplicationSession, self).onDisconnect()

        returnValue(res)

        return None

    @inlineCallbacks
    def flush_logs(self, namespace, log_list):
        res = yield self.publish(u'mdstudio.logger.endpoint.log.{}'.format(namespace), {'logs': log_list},
                                 options=wamp.PublishOptions(acknowledge=True, exclude_me=False))

        returnValue({})

    @chainable
    def _upload_schemas(self):
        schemas = {
            'endpoints': self._collect_schemas('schemas', 'endpoints'),
            'resources': self._collect_schemas('schemas', 'resources')
        }

        yield self.call(u'mdstudio.schema.endpoint.upload', {
            'component': self.component_info['namespace'],
            'schemas': schemas
        }, claims={'vendor': 'mdstudio'})

        self.log.info('Uploaded schemas for {package}', package=self.component_info['package_name'])

    def _collect_schemas(self, *sub_paths):
        schemas = []
        root_dir = os.path.join(self.component_info['module_path'], *sub_paths)

        if os.path.isdir(root_dir):
            for root, dirs, files in os.walk(root_dir):
                if files:
                    for file in files:
                        path = os.path.join(root, file)
                        rel_path = os.path.relpath(path, root_dir).replace('\\', '/')
                        path_decomposition = re.match('(.*?)\\.?(v\\d+)?\\.json', rel_path)

                        with open(path, 'r') as f:
                            schema_entry = {
                                'schema': json.load(f),
                                'name': path_decomposition.group(1)
                            }

                        if path_decomposition.group(2):
                            schema_entry['version'] = int(path_decomposition.group(2).strip('v'))

                        schemas.append(schema_entry)

        return schemas

    @inlineCallbacks
    def _register_scopes(self):
        return_value(True)
        if self.function_scopes:
            res = yield self.call(
                'mdstudio.auth.endpoint.oauth.registerscopes.{}'.format(self.component_info.get('namespace')),
                {'scopes': self.function_scopes})

            self.log.info('Registered {count} scopes for {package}', count=len(self.function_scopes),
                          package=self.component_info['package_name'])

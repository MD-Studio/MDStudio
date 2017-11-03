# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import re

from twisted.logger import LogLevel
from twisted.internet.defer import inlineCallbacks, returnValue
from autobahn import wamp

from mdstudio.application_session import BaseApplicationSession
from mdstudio.util import register, WampSchema, validate_input
from mdstudio.db.model import Model

from twisted.python import log, logfile

from mdstudio.logging import PrintingObserver

# Add global observer for daily logs
# TODO:  make this available without an ugly injection
if os.getenv('MD_GLOBAL_LOG', 0) != 0:
    observer = PrintingObserver(logfile.DailyLogFile('daily.log', os.getenv('MD_GLOBAL_LOG_DIR', './data/logs')))
    log.addObserver(observer)

class LoggerWampApi(BaseApplicationSession):
    """
    Logger management WAMP methods.
    """
    def preInit(self, **kwargs):
        self.session_config['loggernamespace'] = 'logger'

    @inlineCallbacks
    def onRun(self, details):
        self.log_event_subscription = yield self.subscribe(self.log_event, u'mdstudio.logger.endpoint.log', wamp.SubscribeOptions(match='prefix', details_arg='details'))
        yield self.publish(u'mdstudio.logger.endpoint.events.online', True, options=wamp.PublishOptions(acknowledge=True))
        returnValue({})

    @validate_input(WampSchema('logger', 'log/log'))
    @inlineCallbacks
    def log_event(self, request, details=None):
        """
        Receive structured log events over WAMP and broadcast
        to local Twisted logger observers.

        :param event: Structured log event
        :type event:  :py:class:`dict`
        :return:      standard return
        :rtype:       :py:class:`dict` to JSON
        """
        namespace = re.match('^mdstudio\\.logger\\.endpoint\\.log\\.((namespace-)?\\w+)$', details.topic).group(1)

        res = yield Model(self, namespace).insert_many(request['logs'], date_fields=['insert.time'])

    @register(u'mdstudio.logger.endpoint.get', {}, {})
    def get_log_events(self, user):
        """
        Retrieve structured log events from the database
        """

        posts = []
        for post in self.log_collection.find({"authid": user}, {'_id': False}):
            posts.append(post)

        return posts

    def _get_authid(self, details):
        try:
            return details.publisher_authrole if details.publisher_authid is None else details.publisher_authid
        except Exception:
            return 'anonymous'

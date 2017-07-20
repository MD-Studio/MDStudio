# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os

from twisted.logger import LogLevel
from twisted.internet.defer import inlineCallbacks, returnValue
from autobahn import wamp

from lie_componentbase import BaseApplicationSession, register, WampSchema, validate_input


class LoggerWampApi(BaseApplicationSession):
    """
    Logger management WAMP methods.
    """

    @inlineCallbacks
    def onRun(self, details):
        self.log_event_subscription = yield self.subscribe(self.log_event, u'liestudio.logger.log', wamp.SubscribeOptions(match='exact', details_arg='details'))
        # TODO: retrieve events that we have missed during bootup
        # res = yield self.call(u'wamp.subscription.get_events', self.log_event_subscription.id, limit=10)
        returnValue({})

    @validate_input(WampSchema('logger', 'log/log', 1))
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
        authid = self._get_authid(details)

        try:
            res = yield self.call(u'liestudio.db.insertmany', {
                'collection': {
                    'namespace': 'logger', 
                    'name': authid
                },
                'insert': request['logs']
            })
        except Exception as e:
            raise e

    @register(u'liestudio.logger.get', {}, {})
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

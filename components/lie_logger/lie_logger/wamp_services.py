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

from lie_componentbase import BaseApplicationSession, register, WampSchema, validate_input


class LoggerWampApi(BaseApplicationSession):
    """
    Logger management WAMP methods.
    """

    @inlineCallbacks
    def onRun(self, details):
        self.log_event_subscription = yield self.subscribe(self.log_event, u'liestudio.logger.log', wamp.SubscribeOptions(match='prefix', details_arg='details'))
        yield self.publish(u'liestudio.logger.events.online', True, options=wamp.PublishOptions(acknowledge=True))
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
        namespace = re.match('^liestudio\\.logger\\.log\\.(\\w+)$', details.topic).group(1)

        do_log = False

        if details.publisher_authrole == 'oauthclient':
            res = yield self.call(u'liestudio.auth.oauth.client.getusername', {'clientId': authid})
            if res:
                authid = res['username']
                do_log = True
        else:
            do_log = True

        if do_log:
            if namespace != authid:
                namespace = 'namespace-{}'.format(namespace)

            try:
                res = yield self.call(u'liestudio.db.insertmany', {
                    'collection': namespace,
                    'insert': request['logs']
                })
            except Exception as e:
                raise e

        returnValue({})

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

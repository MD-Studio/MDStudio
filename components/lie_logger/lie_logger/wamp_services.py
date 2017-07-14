# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os

from twisted.logger import LogLevel
from twisted.internet.defer import inlineCallbacks, returnValue

from lie_componentbase import BaseApplicationSession, register, WampSchema


class LoggerWampApi(BaseApplicationSession):
    """
    Logger management WAMP methods.
    """

    @register(u'liestudio.logger.log', WampSchema('logger', 'log/log', 1), WampSchema('logger', 'log/log-response', 1), True)
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
            print(res)
            raise e

        if res:
            returnValue({'count': len(res['ids'])})
        else:
            returnValue({'count': 0})

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
        return details.caller_authrole if details.caller_authid is None else details.caller_authid

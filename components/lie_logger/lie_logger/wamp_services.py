# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os

from pymongo import MongoClient
from twisted.logger import LogLevel
from twisted.internet.defer import inlineCallbacks

from lie_componentbase import BaseApplicationSession, register, WampSchema
from settings import settings


class LoggerWampApi(BaseApplicationSession):
    """
    Logger management WAMP methods.
    """

    @register(u'liestudio.logger.log', WampSchema('log', 'insert', 1), {}, True)
    def log_event(self, event, default_log_level='info'):
        """
        Receive structured log events over WAMP and broadcast
        to local Twisted logger observers.

        :param event: Structured log event
        :type event:  :py:class:`dict`
        :return:      standard return
        :rtype:       :py:class:`dict` to JSON
        """

        self.call(u'liestudio.db.insert', )

    @wamp.register(u'liestudio.logger.get')
    def get_log_events(self, user):
        """
        Retrieve structured log events from the database
        """

        posts = []
        for post in self.log_collection.find({"authid": user}, {'_id': False}):
            posts.append(post)

        return posts

# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

from autobahn import wamp

from mdstudio.api.register import register
from mdstudio.component.impl.core import CoreComponentSession
from mdstudio.db.model import Model
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.logging.log_type import LogType


class LoggerComponent(CoreComponentSession):
    """
    Logger management WAMP methods.
    """

    @chainable
    def on_run(self):
        yield self.event(u'mdstudio.logger.endpoint.events.online', True, options=wamp.PublishOptions(acknowledge=True))

    @register('mdstudio.logger.endpoint.log', 'log/log', {})
    @chainable
    def log_event(self, request, claims=None):
        """
        Receive structured log events over WAMP and broadcast
        to local Twisted logger observers.

        :param event: Structured log event
        :type event:  :py:class:`dict`
        :return:      standard return
        :rtype:       :py:class:`dict` to JSON
        """

        res = yield Model(self, self.get_log_collection_name(claims)).insert_many(request['logs'], date_fields=['insert.time'])
        return_value(len(res))

    @register(u'mdstudio.logger.endpoint.get', {}, {})
    def get_log_events(self, user):
        """
        Retrieve structured log events from the database
        """

        posts = []
        for post in self.log_collection.find({"authid": user}, {'_id': False}):
            posts.append(post)

        return posts

    def authorize_request(self, uri, claims):
        connection_type = LogType.from_string(claims['logType'])

        # @todo: solve this using jsonschema
        if connection_type == LogType.User:
            return ('username' in claims) == True
        elif connection_type == LogType.Group:
            return ('groups' in claims) == True # @todo: Properly validate group permissions
        elif connection_type == LogType.GroupRole:
            raise NotImplemented()

        return False

    @staticmethod
    def get_log_collection_name(claims):
        log_type = LogType.from_string(claims['logType'])

        if log_type == LogType.User:
            collection_name = 'users~{user}'.format(user=claims['username'])
        elif log_type == LogType.Group:
            collection_name = 'groups~{group}'.format(group=claims['group'])
        elif log_type == LogType.GroupRole:
            collection_name = 'grouproles~{group}~{group_role}'.format(group=claims['group'], group_role=claims['groupRole'])
        else:
            raise NotImplemented('This distinction does not exist')

        return collection_name

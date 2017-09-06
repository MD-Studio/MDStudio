from collections import defaultdict

import os
import re

from autobahn import wamp
from autobahn.wamp import SubscribeOptions, PublishOptions
from twisted.internet.defer import inlineCallbacks, returnValue

from mdstudio import BaseApplicationSession, register, WampSchema

from .db_methods import MongoClientWrapper, MongoDatabaseWrapper


class DBWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """

    def preInit(self, **kwargs):
        self.session_config_template = {}
        self.package_config_template = WampSchema('db', 'settings/settings')
        self.session_config['loggernamespace'] = 'db'

    def onInit(self, **kwargs):
        dbhost = os.getenv('_LIE_MONGO_HOST', self.package_config.get('dbhost', 'localhost'))
        dbport = self.package_config.get('dbport', 27017)
        self._client = MongoClientWrapper(dbhost, dbport)
        self.autolog = False
        self.autoschema = False

    @inlineCallbacks
    def onRun(self, details):
        yield self.publish(u'mdstudio.db.events.online', True, options=PublishOptions(acknowledge=True))

    @wamp.register(u'mdstudio.db.status')
    def status(self):
        return True

    @register(u'mdstudio.db.more',
              WampSchema('db', 'cursor/more-request', versions={1}),
              WampSchema('db', 'cursor/more-response', versions={1}), details_arg=True, match='prefix', scope='write')
    def more(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return self._client.get_namespace(namespace).more(request['cursorId'])

    @register(u'mdstudio.db.rewind',
              WampSchema('db', 'cursor/rewind-request', versions={1}),
              WampSchema('db', 'cursor/rewind-response', versions={1}), details_arg=True, match='prefix', scope='write')
    def rewind(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return self._client.get_namespace(namespace).rewind(request['cursorId'])

    @register(u'mdstudio.db.insert_one',
              WampSchema('db', 'insert/insert-one-request', versions={1}),
              WampSchema('db', 'insert/insert-one-response', versions={1}), details_arg=True, match='prefix',
              scope='write')
    def insert_one(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)
        kwargs = {}
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).insert_one(request['collection'], request['insert'], **kwargs)

    @register(u'mdstudio.db.insert_many',
              WampSchema('db', 'insert/insert-many-request', versions={1}),
              WampSchema('db', 'insert/insert-many-response', versions={1}), details_arg=True, match='prefix',
              scope='write')
    def insert_many(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)
        kwargs = {}
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).insert_many(request['collection'], request['insert'], **kwargs)

    @register(u'mdstudio.db.replace_one',
              WampSchema('db', 'replace/replace-one-request', versions={1}),
              WampSchema('db', 'replace/replace-one-response', versions={1}), details_arg=True, match='prefix',
              scope='write')
    def replace_one(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)
        kwargs = {
            'upsert': request['upsert']
        }
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).insert_many(request['collection'], request['filter'],
                                                                 request['replacement'], **kwargs)

    @register(u'mdstudio.db.count',
              WampSchema('db', 'count/count-request', versions={1}),
              WampSchema('db', 'count/count-response', versions={1}), details_arg=True, match='prefix', scope='read')
    def count(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        if 'cursor_id' in request:
            kwargs = {
                'cursor_id': request['cursorId'],
                'with_limit_and_skip': request['withLimitAndSkip']
            }

        else:
            kwargs = {
                'collection': request['collection'],
                'filter': request['filter']
            }
            if 'skip' in request:
                kwargs['skip'] = request['skip']
            if 'limit' in request:
                kwargs['limit'] = request['limit']
            if 'fields' in request and 'date' in request['fields']:
                kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).count(**kwargs)

    @register(u'mdstudio.db.update_one',
              WampSchema('db', 'update/update-one-request', versions={1}),
              WampSchema('db', 'update/update-one-response', versions={1}), details_arg=True, match='prefix',
              scope='write')
    def update_one(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).update_one(request['collection'], request['filter'],
                                                                request['update'], **kwargs)

    @register(u'mdstudio.db.update_many',
              WampSchema('db', 'update/update-many-request', versions={1}),
              WampSchema('db', 'update/update-many-response', versions={1}), details_arg=True, match='prefix',
              scope='write')
    def update_many(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).update_many(request['collection'], request['filter'],
                                                                 request['update'], **kwargs)

    @register(u'mdstudio.db.find_one',
              WampSchema('db', 'find/find-one-request', versions={1}),
              WampSchema('db', 'find/find-one-response', versions={1}), details_arg=True, match='prefix', scope='read')
    def find_one(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'skip' in request:
            kwargs['skip'] = request['skip']
        if 'sort' in request:
            kwargs['sort'] = request['sort']
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).find_one(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.find_many',
              WampSchema('db', 'find/find-many-request', versions={1}),
              WampSchema('db', 'find/find-many-response', versions={1}), details_arg=True, match='prefix', scope='read')
    def find_many(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'skip' in request:
            kwargs['skip'] = request['skip']
        if 'limit' in request:
            kwargs['limit'] = request['limit']
        if 'sort' in request:
            kwargs['sort'] = request['sort']
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).find_many(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.find_one_and_update',
              WampSchema('db', 'find/find-one-and-update-request', versions={1}),
              WampSchema('db', 'find/find-one-and-update-response', versions={1}), details_arg=True, match='prefix',
              scope='read')
    def find_one_and_update(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'sort' in request:
            kwargs['sort'] = request['sort']
        if 'return_updated' in request:
            kwargs['return_updated'] = request['return_updated']
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).find_one(request['collection'], request['filter'],
                                                              request['update'], **kwargs)

    @register(u'mdstudio.db.find_one_and_replace',
              WampSchema('db', 'find/find-one-and-replace-request', versions={1}),
              WampSchema('db', 'find/find-one-and-replace-response', versions={1}), details_arg=True, match='prefix',
              scope='read')
    def find_one_and_replace(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'sort' in request:
            kwargs['sort'] = request['sort']
        if 'return_updated' in request:
            kwargs['return_updated'] = request['return_updated']
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).find_one(request['collection'], request['filter'],
                                                              request['replacement'], **kwargs)

    @register(u'mdstudio.db.find_one_and_delete',
              WampSchema('db', 'find/find-one-and-delete-request', versions={1}),
              WampSchema('db', 'find/find-one-and-delete-response', versions={1}), details_arg=True,
              match='prefix',
              scope='read')
    def find_one_and_delete(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'sort' in request:
            kwargs['sort'] = request['sort']

        return self._client.get_namespace(namespace).find_one(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.aggregate',
              WampSchema('db', 'aggregate/aggregate-request', versions={1}),
              WampSchema('db', 'aggregate/aggregate-response', versions={1}), details_arg=True,
              match='prefix',
              scope='read')
    def aggregate(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)
        return self._client.get_namespace(namespace).aggregate(request['collection'], request['pipeline'])


    @register(u'mdstudio.db.delete_one',
              WampSchema('db', 'delete/delete-one', versions={1}),
              WampSchema('db', 'delete/delete-response', versions={1}), details_arg=True, match='prefix',
              scope='delete')
    def delete(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).delete_one(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.delete_many',
              WampSchema('db', 'delete/delete-many', versions={1}),
              WampSchema('db', 'delete/delete-response', versions={1}), details_arg=True, match='prefix',
              scope='delete')
    def delete_many(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'fields' in request and 'date' in request['fields']:
            kwargs['date_fields'] = request['fields']['date']

        return self._client.get_namespace(namespace).delete_many(request['collection'], request['filter'], **kwargs)

    def _extract_namespace(self, uri):
        return re.match('mdstudio.db.\\w+\\.(.*)', uri).group(1)

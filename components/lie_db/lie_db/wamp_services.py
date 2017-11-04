import os
import re
from autobahn import wamp
from autobahn.wamp import PublishOptions

from mdstudio.api.register import register
from mdstudio.api.schema import WampSchema
from mdstudio.application_session import BaseApplicationSession
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from .mongo_client_wrapper import MongoClientWrapper


class DBWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """

    def preInit(self, **kwargs):
        self.session_config_template = {}
        self.package_config_template = WampSchema('db', 'settings/settings')
        self.session_config['loggernamespace'] = 'db'

    def onInit(self, **kwargs):
        db_host = os.getenv('MD_MONGO_HOST', self.package_config.get('host', 'localhost'))
        db_port = int(os.getenv('MD_MONGO_PORT', self.package_config.get('port', 27017)))
        self._client = MongoClientWrapper(db_host, db_port)
        self.autolog = False
        self.autoschema = False

    @chainable
    def onRun(self, details):
        self.publish_options = PublishOptions(acknowledge=True)
        yield self.publish(u'mdstudio.db.endpoint.events.online', True, options=self.publish_options)

    @register(u'mdstudio.db.endpoint.more', 'cursor/more-request/v1', 'cursor/more-response/v1', match='prefix', scope='write')
    def more(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return self._client.get_namespace(namespace).more(request['cursorId'])

    @register(u'mdstudio.db.endpoint.rewind',
              WampSchema('db', 'cursor/rewind-request'),
              WampSchema('db', 'cursor/rewind-response'), match='prefix', scope='write')
    def rewind(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return self._client.get_namespace(namespace).rewind(request['cursorId'])

    @register(u'mdstudio.db.endpoint.insert_one',
              WampSchema('db', 'insert/insert-one-request'),
              WampSchema('db', 'insert/insert-one-response'), match='prefix',
              scope='write')
    def insert_one(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)
        kwargs = {}
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).insert_one(request['collection'], request['insert'], **kwargs)

    @register(u'mdstudio.db.endpoint.insert_many',
              WampSchema('db', 'insert/insert-many-request'),
              WampSchema('db', 'insert/insert-many-response'), match='prefix',
              scope='write')
    def insert_many(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)
        kwargs = {}
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).insert_many(request['collection'], request['insert'], **kwargs)

    @register(u'mdstudio.db.endpoint.replace_one',
              WampSchema('db', 'replace/replace-one-request'),
              WampSchema('db', 'replace/replace-one-response'), match='prefix',
              scope='write')
    def replace_one(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)
        kwargs = {}
        if 'upsert' in request :
            kwargs['upsert'] = request['upsert']
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).replace_one(request['collection'], request['filter'],
                                                                 request['replacement'], **kwargs)

    @register(u'mdstudio.db.endpoint.count',
              WampSchema('db', 'count/count-request'),
              WampSchema('db', 'count/count-response'), match='prefix', scope='read')
    def count(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        if 'cursorId' in request:
            kwargs = {
                'cursor_id': request['cursorId'],
                'with_limit_and_skip': request['withLimitAndSkip']
            }

        else:
            kwargs = {
                'collection': request['collection'],
                'filter': request.get('filter', {})
            }
            if 'skip' in request:
                kwargs['skip'] = request['skip']
            if 'limit' in request:
                kwargs['limit'] = request['limit']
            if 'fields' in request and 'datetime' in request['fields']:
                kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).count(**kwargs)

    @register(u'mdstudio.db.endpoint.update_one',
              WampSchema('db', 'update/update-one-request'),
              WampSchema('db', 'update/update-one-response'), match='prefix',
              scope='write')
    def update_one(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).update_one(request['collection'], request['filter'],
                                                                request['update'], **kwargs)

    @register(u'mdstudio.db.endpoint.update_many',
              WampSchema('db', 'update/update-many-request'),
              WampSchema('db', 'update/update-many-response'), match='prefix',
              scope='write')
    def update_many(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).update_many(request['collection'], request['filter'],
                                                                 request['update'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_one',
              WampSchema('db', 'find/find-one-request'),
              WampSchema('db', 'find/find-one-response'), match='prefix', scope='read')
    def find_one(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'skip' in request:
            kwargs['skip'] = request['skip']
        if 'sort' in request:
            kwargs['sort'] = request['sort']
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).find_one(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_many',
              WampSchema('db', 'find/find-many-request'),
              WampSchema('db', 'find/find-many-response'), match='prefix', scope='read')
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
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).find_many(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_one_and_update',
              WampSchema('db', 'find/find-one-and-update-request'),
              WampSchema('db', 'find/find-one-and-update-response'), match='prefix',
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
        if 'returnUpdated' in request:
            kwargs['return_updated'] = request['returnUpdated']
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).find_one_and_update(request['collection'], request['filter'],
                                                              request['update'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_one_and_replace',
              WampSchema('db', 'find/find-one-and-replace-request'),
              WampSchema('db', 'find/find-one-and-replace-response'), match='prefix',
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
        if 'returnUpdated' in request:
            kwargs['return_updated'] = request['returnUpdated']
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).find_one_and_replace(request['collection'], request['filter'],
                                                              request['replacement'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_one_and_delete',
              WampSchema('db', 'find/find-one-and-delete-request'),
              WampSchema('db', 'find/find-one-and-delete-response'),
              match='prefix',
              scope='read')
    def find_one_and_delete(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'sort' in request:
            kwargs['sort'] = request['sort']
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).find_one_and_delete(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.endpoint.distinct',
              WampSchema('db', 'distinct/distinct-request'),
              WampSchema('db', 'distinct/distinct-response'),
              match='prefix',
              scope='read')
    def distinct(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'filter' in request:
            kwargs['filter'] = request['filter']
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).distinct(request['collection'], request['field'], **kwargs)

    @register(u'mdstudio.db.endpoint.aggregate',
              WampSchema('db', 'aggregate/aggregate-request'),
              WampSchema('db', 'aggregate/aggregate-response'),
              match='prefix',
              scope='read')
    def aggregate(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)
        return self._client.get_namespace(namespace).aggregate(request['collection'], request['pipeline'])


    @register(u'mdstudio.db.endpoint.delete_one',
              WampSchema('db', 'delete/delete-one'),
              WampSchema('db', 'delete/delete-response'), match='prefix',
              scope='delete')
    def delete_one(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).delete_one(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.endpoint.delete_many',
              WampSchema('db', 'delete/delete-many'),
              WampSchema('db', 'delete/delete-response'), match='prefix',
              scope='delete')
    def delete_many(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        kwargs = {}
        if 'fields' in request and 'datetime' in request['fields']:
            kwargs['date_fields'] = request['fields']['datetime']

        return self._client.get_namespace(namespace).delete_many(request['collection'], request['filter'], **kwargs)

    def _extract_namespace(self, uri):
        return re.match('mdstudio.db.endpoint.\\w+\\.(.*)', uri).group(1)

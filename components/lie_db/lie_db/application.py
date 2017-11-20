import os
from autobahn.wamp import PublishOptions

from mdstudio.api.register import register
from mdstudio.component.impl.core import CoreComponentSession
from mdstudio.db.connection import ConnectionType
from mdstudio.db.fields import Fields
from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.lock import Lock


class DBComponent(CoreComponentSession):
    """
    Database management WAMP methods.
    """

    def on_init(self):
        db_host = os.getenv('MD_MONGO_HOST', self.component_config.settings.get('host', 'localhost'))
        db_port = int(os.getenv('MD_MONGO_PORT', self.component_config.settings.get('port', 27017)))
        self._client = MongoClientWrapper(db_host, db_port)
        self.autolog = False
        self.autoschema = False

        self.database_lock = Lock()

    @chainable
    def on_run(self):
        self.publish_options = PublishOptions(acknowledge=True)
        yield self.event(u'mdstudio.db.endpoint.events.online', True, options=self.publish_options)

    @register(u'mdstudio.db.endpoint.more', 'cursor/more-request/v1', 'cursor/more-response/v1', scope='write')
    def more(self, request, claims=None):
        database = self.get_database(claims)

        return database.more(request['cursorId'])

    @register(u'mdstudio.db.endpoint.rewind',
              'cursor/rewind-request',
              'cursor/rewind-response', scope='write')
    def rewind(self, request, claims=None):
        database = self.get_database(claims)

        return database.rewind(request['cursorId'])

    @register(u'mdstudio.db.endpoint.insert_one',
              'insert/insert-one-request',
              'insert/insert-one-response',
              scope='write')
    def insert_one(self, request, claims=None):
        database = self.get_database(claims)
        kwargs = {}

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.insert_one(request['collection'], request['insert'], **kwargs)

    @register(u'mdstudio.db.endpoint.insert_many',
              'insert/insert-many-request',
              'insert/insert-many-response',
              scope='write')
    def insert_many(self, request, claims=None):
        database = self.get_database(claims)
        kwargs = {}

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.insert_many(request['collection'], request['insert'], **kwargs)

    @register(u'mdstudio.db.endpoint.replace_one',
              'replace/replace-one-request',
              'replace/replace-one-response',
              scope='write')
    def replace_one(self, request, claims=None):
        database = self.get_database(claims)
        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.replace_one(request['collection'], request['filter'],
                                    request['replacement'], **kwargs)

    @register(u'mdstudio.db.endpoint.count',
              'count/count-request',
              'count/count-response', scope='read')
    def count(self, request, claims=None):
        database = self.get_database(claims)

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
            if 'fields' in request:
                kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.count(**kwargs)

    @register(u'mdstudio.db.endpoint.update_one',
              'update/update-one-request',
              'update/update-one-response',
              scope='write')
    def update_one(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.update_one(request['collection'], request['filter'],
                                   request['update'], **kwargs)

    @register(u'mdstudio.db.endpoint.update_many',
              'update/update-many-request',
              'update/update-many-response',
              scope='write')
    def update_many(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.update_many(request['collection'], request['filter'],
                                    request['update'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_one',
              'find/find-one-request',
              'find/find-one-response', scope='read')
    def find_one(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'skip' in request:
            kwargs['skip'] = request['skip']
        if 'sort' in request:
            kwargs['sort'] = request['sort']

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.find_one(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_many',
              'find/find-many-request',
              'find/find-many-response', scope='read')
    def find_many(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'skip' in request:
            kwargs['skip'] = request['skip']
        if 'limit' in request:
            kwargs['limit'] = request['limit']
        if 'sort' in request:
            kwargs['sort'] = request['sort']

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.find_many(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_one_and_update',
              'find/find-one-and-update-request',
              'find/find-one-and-update-response',
              scope='read')
    def find_one_and_update(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'sort' in request:
            kwargs['sort'] = request['sort']
        if 'returnUpdated' in request:
            kwargs['return_updated'] = request['returnUpdated']

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.find_one_and_update(request['collection'], request['filter'],
                                            request['update'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_one_and_replace',
              'find/find-one-and-replace-request',
              'find/find-one-and-replace-response',
              scope='read')
    def find_one_and_replace(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'sort' in request:
            kwargs['sort'] = request['sort']
        if 'returnUpdated' in request:
            kwargs['return_updated'] = request['returnUpdated']

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.find_one_and_replace(request['collection'], request['filter'],
                                             request['replacement'], **kwargs)

    @register(u'mdstudio.db.endpoint.find_one_and_delete',
              'find/find-one-and-delete-request',
              'find/find-one-and-delete-response',
              scope='read')
    def find_one_and_delete(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'projection' in request:
            kwargs['projection'] = request['projection']
        if 'sort' in request:
            kwargs['sort'] = request['sort']

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.find_one_and_delete(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.endpoint.distinct',
              'distinct/distinct-request',
              'distinct/distinct-response',
              scope='read')
    def distinct(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'filter' in request:
            kwargs['filter'] = request['filter']

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.distinct(request['collection'], request['field'], **kwargs)

    @register(u'mdstudio.db.endpoint.aggregate',
              'aggregate/aggregate-request',
              'aggregate/aggregate-response',
              scope='read')
    def aggregate(self, request, claims=None):
        database = self.get_database(claims)
        return database.aggregate(request['collection'], request['pipeline'])

    @register(u'mdstudio.db.endpoint.delete_one',
              'delete/delete-one',
              'delete/delete-response',
              scope='delete')
    def delete_one(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.delete_one(request['collection'], request['filter'], **kwargs)

    @register(u'mdstudio.db.endpoint.delete_many',
              'delete/delete-many',
              'delete/delete-response',
              scope='delete')
    def delete_many(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}

        if 'fields' in request:
            kwargs['fields'] = Fields().from_dict(request['fields'])

        return database.delete_many(request['collection'], request['filter'], **kwargs)

    @chainable
    def get_database(self, claims):
        connection_type = ConnectionType.from_string(claims['connectionType'])

        if connection_type == ConnectionType.User:
            database_name = 'users~{user}'.format(user=claims['username'])
        elif connection_type == ConnectionType.Group:
            database_name = 'groups~{group}'.format(group=claims['group'])
        elif connection_type == ConnectionType.GroupRole:
            database_name = 'grouproles~{group}~{group_role}'.format(group=claims['group'], group_role=claims['groupRole'])
        else:
            raise NotImplemented('This distinction does not exist')

        result = None
        if database_name:
            yield self.database_lock.acquire()
            result = self._client.get_database(database_name)
            yield self.database_lock.release()

        return result

    def authorize_request(self, uri, claims):
        connection_type = ConnectionType.from_string(claims['connectionType'])

        # @todo: solve this using jsonschema
        # @todo: authorize cursor
        if connection_type == ConnectionType.User:
            return ('username' in claims) == True
        elif connection_type == ConnectionType.Group:
            raise NotImplemented()
        elif connection_type == ConnectionType.GroupRole:
            raise NotImplemented()

        return False

from collections import OrderedDict

import base64
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from mdstudio.db.database import IDatabase

from db.key_repository import KeyRepository
from mdstudio.api.endpoint import endpoint
from mdstudio.component.impl.core import CoreComponentSession
from mdstudio.db.connection_type import ConnectionType
from mdstudio.db.fields import Fields
from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from mdstudio.db.index import Index
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.lock import Lock
from mdstudio.deferred.return_value import return_value


class DBComponent(CoreComponentSession):
    """
    Database management WAMP methods.
    """

    def pre_init(self):

        self.load_environment(OrderedDict([
            ('host', (['MD_MONGO_HOST'], None)),
            ('port', (['MD_MONGO_PORT'], None, int)),
            ('secret', (['MD_MONGO_SECRET'], None))
        ]))

        self.component_waiters.append(self.ComponentWaiter(self, 'schema', self.group_context('mdstudio')))

        self._client = MongoClientWrapper(self.component_config.settings['host'], self.component_config.settings['port'])

        super(DBComponent, self).pre_init()

    def on_init(self):

        assert self.component_config.settings['secret'], 'The database must have a secret set!\n' \
                                                         'Please modify your configuration or set "MD_MONGO_SECRET"'
        assert len(self.component_config.settings['secret']) >= 20, 'The database secret must be at least 20 characters long! ' \
                                                                    'Please make sure it is larger than it is now.'
        self._set_secret()

        self.database_lock = Lock()

    @property
    def secret(self):
        return self._secret

    @chainable
    def _on_join(self):
        yield self.call('mdstudio.auth.endpoint.ring0.set-status', {'status': True})

        yield super(DBComponent, self)._on_join()

    @endpoint('more', 'cursor/more-request/v1', 'cursor/more-response/v1', scope='write')
    def more(self, request, claims=None):
        database = self.get_database(claims)

        return database.more(request['cursorId'], claims=claims)

    @endpoint('rewind',
              'cursor/rewind-request',
              'cursor/rewind-response', scope='write')
    def rewind(self, request, claims=None):
        database = self.get_database(claims)

        return database.rewind(request['cursorId'], claims=claims)

    @endpoint('insert_one',
              'insert/insert-one-request',
              'insert/insert-one-response',
              scope='write')
    def insert_one(self, request, claims=None):
        database = self.get_database(claims)
        kwargs = {}

        self.set_fields(claims, kwargs, request)

        return database.insert_one(request['collection'], request['insert'], **kwargs)

    @endpoint('insert_many',
              'insert/insert-many-request',
              'insert/insert-many-response',
              scope='write')
    def insert_many(self, request, claims=None):
        database = self.get_database(claims)
        kwargs = {}

        self.set_fields(claims, kwargs, request)

        return database.insert_many(request['collection'], request['insert'], **kwargs)

    @endpoint('replace_one',
              'replace/replace-one-request',
              'replace/replace-one-response',
              scope='write')
    def replace_one(self, request, claims=None):
        database = self.get_database(claims)
        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']

        self.set_fields(claims, kwargs, request)

        return database.replace_one(request['collection'], request['filter'],
                                    request['replacement'], **kwargs)

    @endpoint('count',
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
                kwargs['fields'] = Fields.from_dict(request['fields'])

        return database.count(**kwargs)

    @endpoint('update_one',
              'update/update-one-request',
              'update/update-one-response',
              scope='write')
    def update_one(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']

        self.set_fields(claims, kwargs, request)

        return database.update_one(request['collection'], request['filter'],
                                   request['update'], **kwargs)

    @endpoint('update_many',
              'update/update-many-request',
              'update/update-many-response',
              scope='write')
    def update_many(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'upsert' in request:
            kwargs['upsert'] = request['upsert']

        self.set_fields(claims, kwargs, request)

        return database.update_many(request['collection'], request['filter'],
                                    request['update'], **kwargs)

    @endpoint('find_one',
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

        self.set_fields(claims, kwargs, request)

        return database.find_one(request['collection'], request['filter'], **kwargs)

    @endpoint('find_many',
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

        self.set_fields(claims, kwargs, request)

        return database.find_many(request['collection'], request['filter'], **kwargs)

    @endpoint('find_one_and_update',
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

        self.set_fields(claims, kwargs, request)

        return database.find_one_and_update(request['collection'], request['filter'],
                                            request['update'], **kwargs)

    @endpoint('find_one_and_replace',
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

        self.set_fields(claims, kwargs, request)

        return database.find_one_and_replace(request['collection'], request['filter'],
                                             request['replacement'], **kwargs)

    @endpoint('find_one_and_delete',
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

        self.set_fields(claims, kwargs, request)

        return database.find_one_and_delete(request['collection'], request['filter'], **kwargs)

    @endpoint('distinct',
              'distinct/distinct-request',
              'distinct/distinct-response',
              scope='read')
    def distinct(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}
        if 'filter' in request:
            kwargs['filter'] = request['filter']

        self.set_fields(claims, kwargs, request)

        return database.distinct(request['collection'], request['field'], **kwargs)

    @endpoint('aggregate',
              'aggregate/aggregate-request',
              'aggregate/aggregate-response',
              scope='read')
    def aggregate(self, request, claims=None):
        database = self.get_database(claims)
        return database.aggregate(request['collection'], request['pipeline'])

    @endpoint('delete_one',
              'delete/delete-one',
              'delete/delete-response',
              scope='delete')
    def delete_one(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}

        self.set_fields(claims, kwargs, request)

        return database.delete_one(request['collection'], request['filter'], **kwargs)

    @endpoint('delete_many',
              'delete/delete-many',
              'delete/delete-response',
              scope='delete')
    def delete_many(self, request, claims=None):
        database = self.get_database(claims)

        kwargs = {}

        self.set_fields(claims, kwargs, request)

        return database.delete_many(request['collection'], request['filter'], **kwargs)

    @endpoint('create_indexes',
              'index/create-request/v1',
              'index/create-response/v1',
              scope='index')
    def create_indexes(self, request, claims=None):
        database = self.get_database(claims)

        return database.create_indexes(request['collection'], [Index.from_dict(d) for d in request['indexes']])

    @endpoint('drop-indexes',
              'index/drop-request/v1',
              scope='index')
    def drop_indexes(self, request, claims=None):
        database = self.get_database(claims)

        return database.drop_indexes(request['collection'], [Index.from_dict(d) for d in request['indexes']])

    @endpoint('drop-all-indexes',
              'index/drop-all-request/v1',
              scope='index')
    def drop_all_indexes(self, request, claims=None):
        database = self.get_database(claims)

        return database.drop_all_indexes(request['collection'])

    @chainable
    def get_database(self, claims):
        # type: (dict) -> IDatabase
        connection_type = ConnectionType.from_string(claims['connectionType'])

        if connection_type == ConnectionType.User:
            database_name = 'users~{user}'.format(user=claims['username'])

            assert database_name.count('~') <= 1, 'Someone tried to spoof the key database!'
        elif connection_type == ConnectionType.Group:
            database_name = 'groups~{group}'.format(group=claims['group'])

            assert database_name.count('~') <= 1, 'Someone tried to spoof the key database!'
        elif connection_type == ConnectionType.GroupRole:
            database_name = 'grouproles~{group}~{group_role}'.format(group=claims['group'], group_role=claims['role'])

            assert database_name.count('~') <= 2, 'Someone tried to spoof the key database!'
        else:
            raise NotImplementedError('This distinction does not exist')

        result = None
        if database_name:
            assert database_name.strip() != 'users~db', 'Someone tried to spoof the key database!'

            yield self.database_lock.acquire()
            result = self._client.get_database(database_name)
            yield self.database_lock.release()

        return_value(result)

    def set_fields(self, claims, kwargs, request):
        if 'fields' in request:
            repo = KeyRepository(self, self._client.get_database('users~db'))
            kwargs['fields'] = Fields.from_dict(request['fields'], repo)
            if kwargs['fields'].uses_encryption:
                kwargs['claims'] = claims

    def authorize_request(self, uri, claims):
        connection_type = ConnectionType.from_string(claims['connectionType'])

        # @todo: solve this using jsonschema
        # @todo: authorize cursor
        if connection_type == ConnectionType.User:
            return ('username' in claims) == True
        elif connection_type == ConnectionType.Group:
            return ('group' in claims) == True
        elif connection_type == ConnectionType.GroupRole:
            return all(key in claims for key in ['group', 'role'])

        return False

    def _set_secret(self):
        secret = self.component_config.settings['secret'].encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=hashlib.sha512(secret).digest(),
            iterations=150000,
            backend=default_backend()
        )
        self._secret = base64.urlsafe_b64encode(kdf.derive(secret))

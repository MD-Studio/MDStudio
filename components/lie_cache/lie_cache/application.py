from collections import OrderedDict

from mdstudio.api.endpoint import endpoint
from mdstudio.component.impl.core import CoreComponentSession
from rediscluster import StrictRedisCluster

from mdstudio.db.connection import ConnectionType
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


class CacheComponent(CoreComponentSession):

    def on_init(self):
        startup_nodes = self.component_config.settings['nodes']

        self.rc = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
        self.component_waiters.append(self.ComponentWaiter(self, 'schema'))

    @chainable
    def _on_join(self):
        yield self.call('mdstudio.auth.endpoint.ring0.set-status', {'status': True})

        yield super(CacheComponent, self)._on_join()


    @endpoint(u'mdstudio.cache.endpoint.set', 'set/set-request/v1', {}, scope='write')
    def set(self, request, claims=None):
        database = self.get_database(claims)
        key = '{}~{}'.format(database, request['key'])
        return self.rc.setex(key, request['value'], request['expiry'])

    @chainable
    def get_database(self, claims):
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
            raise NotImplemented('This distinction does not exist')

        result = None
        if database_name:
            assert database_name.strip() != 'users~db', 'Someone tried to spoof the key database!'

            yield self.database_lock.acquire()
            result = self._client.get_database(database_name)
            yield self.database_lock.release()

        return_value(result)

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
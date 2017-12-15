from rediscluster import StrictRedisCluster

from mdstudio.api.endpoint import endpoint
from mdstudio.cache.impl.redis_client_wrapper import RedisClientWrapper
from mdstudio.component.impl.core import CoreComponentSession
from mdstudio.db.connection_type import ConnectionType
from mdstudio.deferred.chainable import chainable


class CacheComponent(CoreComponentSession):

    def on_init(self):
        startup_nodes = self.component_config.settings['nodes']

        self._rc = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
        self._cache = RedisClientWrapper(self._rc)
        self.component_waiters.append(self.ComponentWaiter(self, 'schema'))

    @chainable
    def _on_join(self):
        yield self.call('mdstudio.auth.endpoint.ring0.set-status', {'status': True})

        yield super(CacheComponent, self)._on_join()

    @endpoint(u'mdstudio.cache.endpoint.put', 'put/put-request/v1', 'put/put-response/v1', scope='write')
    def put(self, request, claims=None):
        if 'key' in request:
            key = self.get_key(request['key'], claims)
            return self._cache.put(key, request['value'], request.get('expiry'))
        else:
            values = []
            for key in request['keyValues']:
                values.append((self.get_key(key['key'], claims), key['value']))
            return self._cache.put_many(values, request.get('expiry'))

    @endpoint(u'mdstudio.cache.endpoint.get', 'get/get-request/v1', 'get/get-response/v1', scope='read')
    def get(self, request, claims=None):
        key = self.get_key(request['key'], claims)
        return self._cache.get(key)

    @endpoint(u'mdstudio.cache.endpoint.extract', 'extract/extract-request/v1', 'extract/extract-response/v1', scope='write')
    def extract(self, request, claims=None):
        key = self.extract_key(request['key'], claims)
        return self._cache.extract(key)

    @endpoint(u'mdstudio.cache.endpoint.has', 'has/has-request/v1', 'has/has-response/v1', scope='read')
    def has(self, request, claims=None):
        key = self.has_key(request['key'], claims)
        return self._cache.has(key)

    @endpoint(u'mdstudio.cache.endpoint.touch', 'touch/touch-request/v1', 'touch/touch-response/v1', scope='write')
    def touch(self, request, claims=None):
        if 'key' in request:
            keys = self.get_key(request['key'], claims)
        else:
            keys = [self.get_key(key, claims) for key in request['keys']]

        return self._cache.touch(keys)

    @endpoint(u'mdstudio.cache.endpoint.forget', 'forget/forget-request/v1', 'forget/forget-response/v1', scope='write')
    def forget(self, request, claims=None):
        if 'key' in request:
            keys = self.get_key(request['key'], claims)
        else:
            keys = [self.get_key(key, claims) for key in request['keys']]

        return self._cache.forget(keys)

    def get_key(self, key, claims):
        connection_type = ConnectionType.from_string(claims['connectionType'])

        if connection_type == ConnectionType.User:
            namespace = 'users:{user}'.format(user=claims['username'])

            assert namespace.count(':') <= 1, 'Someone tried to spoof the cache!'
        elif connection_type == ConnectionType.Group:
            namespace = 'groups:{group}'.format(group=claims['group'])

            assert namespace.count(':') <= 1, 'Someone tried to spoof the cache!'
        elif connection_type == ConnectionType.GroupRole:
            namespace = 'grouproles:{group}:{group_role}'.format(group=claims['group'], group_role=claims['role'])

            assert namespace.count(':') <= 2, 'Someone tried to spoof the cache!'
        else:
            raise NotImplemented('This distinction does not exist')

        return '{}:{}'.format(namespace, key)

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

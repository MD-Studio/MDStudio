from typing import Any, Union, List, Tuple, Optional

from mdstudio.cache.cache import ICache
from mdstudio.deferred.make_deferred import make_deferred


class RedisClientWrapper(ICache):

    def __init__(self, client):
        # type: (StrictRedisCluster) -> None

        # type: StrictRedisCluster
        self.client = client

    @make_deferred
    def put(self, key, value, expiry=None):

        return {
            'success': self.client.setex(key, expiry, value)
        }

    @make_deferred
    def put_many(self, values, expiry=None):
        # type: (List[Tuple[str, Any]], Optional[int]) -> dict

        success = True

        with self.client.pipeline() as pipe:
            for v in values:
                success = success and pipe.setex(v[0], expiry, v[1])

        return {
            'success': success
        }

    @make_deferred
    def extract(self, key):
        # type: (str) -> dict

        with self.client.pipeline() as pipe:
            result = pipe.get(key)
            pipe.delete()

        return {
            'result': result
        }

    @make_deferred
    def get(self, key):
        # type: (str) -> dict

        return {
            'result': self.client.get(key)
        }

    @make_deferred
    def has(self, key):
        # type: (str) -> dict

        return {
            'has': self.client.exists(key)
        }

    @make_deferred
    def touch(self, keys):
        # type: (Union[List[str], str]) -> dict
        if isinstance(keys, list):
            count = self.client.touch(*keys)
        else:
            count = self.client.touch(keys)

        return {
            'touched': count
        }

    @make_deferred
    def forget(self, keys):
        # type: (Union[List[str], str]) -> dict
        if isinstance(keys, list):
            count = self.client.delete(*keys)
        else:
            count = self.client.delete(keys)

        return {
            'forgotten': count
        }

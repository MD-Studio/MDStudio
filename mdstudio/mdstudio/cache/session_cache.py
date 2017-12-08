from typing import Optional, Any, List, Union, Tuple

from mdstudio.cache.cache import ICache
from mdstudio.cache.connection import ConnectionType


class SessionCacheWrapper(ICache):

    def __init__(self, session, connection_type=ConnectionType.User):
        # type: (CommonSession, ConnectionType) -> None
        self.session = session  # type: CommonSession
        self.connection_type = connection_type

    def put(self, key, value, expiry=None):
        # type: (str, Any, Optional[int]) -> dict

        request = {
            'key': key,
            'value': value
        }
        if expiry:
            request['expiry'] = expiry

        return self._call('put', request)

    def put_many(self, values, expiry=None):
        # type: (List[Tuple[str, Any]], Optional[int]) -> dict

        values = []
        for v in values:
            values.append({
                'key': v[0],
                'value': v[1]
            })

        request = {
            'keyValues': values
        }
        if expiry:
            request['expiry'] = expiry

        return self._call('put', request)

    def get(self, key):
        # type: (str) -> dict
        return self._call('get', {
            'key': key
        })

    def forget(self, keys):
        # type: (Union[List[str], str]) -> dict
        if isinstance(keys, list):
            request = {'keys': keys}
        else:
            request = {'key': keys}
        return self._call('forget', request)

    def _call(self, uri, request):
        return self.session.call('mdstudio.cache.endpoint.{}'.format(uri), request, claims=self.session.call_context.get_cache_claims(self.connection_type))
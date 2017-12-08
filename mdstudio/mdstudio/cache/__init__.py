from typing import Optional, List, Tuple, Any, Union

from mdstudio.cache.cache import ICache
from mdstudio.cache.cache_type import CacheType
from mdstudio.cache.impl.connection import GlobalCache


class Cache(object):
    # type: ICache
    wrapper = None

    # type: CacheType
    cache_type = CacheType.User

    def __init__(self, wrapper=None, cache_type=None):
        # type: (Optional[ICache], Optional[CacheType]) -> None
        self._check_wrapper(wrapper)
        self.wrapper = wrapper or GlobalCache.get_wrapper(cache_type or self.cache_type)

    def set(self, key, value, expiry=None):
        # type: (str, Any, Optional[int]) -> bool
        return self.wrapper.set(key, value, expiry)['success']

    def set_many(self, values, expiry=None):
        # type: (List[Tuple[str, Any]], Optional[int]) -> bool
        return self.wrapper.set(values, expiry)['success']

    def get(self, key):
        # type: (str) -> Any
        return self.wrapper.get(key)['result']

    def delete(self, keys):
        # type: (Union[List[str], str]) -> int
        return self.wrapper.get(keys)['count']

    def _check_wrapper(self, wrapper):
        assert isinstance(wrapper, ICache), 'Wrapper should inherit ICache'

import six

from mdstudio.api.singleton import Singleton
from mdstudio.cache.session_cache import SessionCacheWrapper
from mdstudio.session import GlobalSession


@six.add_metaclass(Singleton)
class GlobalCache(object):
    def __init__(self):
        assert GlobalSession().session, "Tried to get session without initialising first"
        self._session = GlobalSession().session

    @staticmethod
    def get_wrapper(connection_type):
        return SessionCacheWrapper(GlobalCache()._session, connection_type)

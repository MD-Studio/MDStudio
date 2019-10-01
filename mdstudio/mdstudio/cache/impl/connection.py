import six

from mdstudio.api.singleton import Singleton
from mdstudio.cache.session_cache import SessionCacheWrapper
from mdstudio.session import GlobalSession
from mdstudio.util.exception import MDStudioException


@six.add_metaclass(Singleton)
class GlobalCache(object):
    def __init__(self):

        try:
            self._session = GlobalSession().session
        except Exception:
            raise MDStudioException("Tried to get session without initialising first")

    @staticmethod
    def get_wrapper(connection_type):
        return SessionCacheWrapper(GlobalCache()._session, connection_type)

import six

from mdstudio.api.singleton import Singleton
from mdstudio.db.session_database import SessionDatabaseWrapper
from mdstudio.session import GlobalSession


@six.add_metaclass(Singleton)
class GlobalConnection(object):
    def __init__(self):
        assert GlobalSession().session, "Tried to get session without initialising first"
        self._session = GlobalSession().session

    @staticmethod
    def get_wrapper(connection_type):
        return SessionDatabaseWrapper(GlobalConnection()._session, connection_type)

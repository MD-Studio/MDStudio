import six

from mdstudio.api.singleton import Singleton
from mdstudio.db.session_database import SessionDatabaseWrapper


@six.add_metaclass(Singleton)
class GlobalConnection(object):
    def __init__(self, session=None):
        assert session, "Tried to get session without initialising first"
        self._session = session

    def get_wrapper(self, connection_type):
        return SessionDatabaseWrapper(self._session, connection_type)

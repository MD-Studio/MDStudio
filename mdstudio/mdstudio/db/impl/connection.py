import six

from mdstudio.api.singleton import Singleton
from mdstudio.db.session_database import SessionDatabaseWrapper
from mdstudio.session import GlobalSession
from mdstudio.util.exception import MDStudioException


@six.add_metaclass(Singleton)
class GlobalConnection(object):
    def __init__(self):

        try:
            self._session = GlobalSession().session
        except Exception:
            raise MDStudioException('Tried to get session without initialising first')

    @staticmethod
    def get_wrapper(connection_type):
        return SessionDatabaseWrapper(GlobalConnection()._session, connection_type)

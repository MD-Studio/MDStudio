import six

from mdstudio.api.singleton import Singleton
from mdstudio.util.exception import MDStudioException


@six.add_metaclass(Singleton)
class GlobalSession(object):
    def __init__(self, session=None):
        if not session:
            raise MDStudioException('Tried to get session without initialising first')
        self._session = session

    @property
    def session(self):
        return self._session

import six

from mdstudio.api.singleton import Singleton


@six.add_metaclass(Singleton)
class GlobalSession(object):
    def __init__(self, session=None):
        assert session, "Tried to get session without initialising first"
        self._session = session

    @property
    def session(self):
        return self._session

from unittest import TestCase

from mdstudio.db.connection import ConnectionType
from mdstudio.db.impl.connection import GlobalConnection
from mdstudio.db.session_database import SessionDatabaseWrapper


class GlobalConnectionTest(TestCase):

    def test_construction(self):
        connection = GlobalConnection({'test': {'testobject'}})

        self.assertEqual(connection._session, {'test': {'testobject'}})
        self.assertIs(connection, GlobalConnection())


    def test_get_wrapper(self):
        connection = GlobalConnection({'test': {'testobject'}})
        result = connection.get_wrapper(ConnectionType.User)
        self.assertIsInstance(result, SessionDatabaseWrapper)
        self.assertEqual(result.session, {'test': {'testobject'}})


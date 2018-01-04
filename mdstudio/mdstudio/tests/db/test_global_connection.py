from unittest import TestCase

from mdstudio.db.connection_type import ConnectionType
from mdstudio.db.impl.connection import GlobalConnection
from mdstudio.db.session_database import SessionDatabaseWrapper
from mdstudio.session import GlobalSession


class GlobalConnectionTest(TestCase):

    def setUp(self):
        GlobalConnection._instance = None
        GlobalSession({'test': {'testobject'}})

    def tearDown(self):
        GlobalConnection._instance = None
        GlobalSession._instance = None

    def test_construction(self):
        connection = GlobalConnection()

        self.assertEqual(connection._session, {'test': {'testobject'}})
        self.assertIs(connection, GlobalConnection())

    def test_get_wrapper(self):
        connection = GlobalConnection()
        result = connection.get_wrapper(ConnectionType.User)
        self.assertIsInstance(result, SessionDatabaseWrapper)
        self.assertEqual(result.session, {'test': {'testobject'}})

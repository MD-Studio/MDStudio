from mock import mock
import pymongo
import mongomock

from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from mdstudio.db.impl.mongo_database_wrapper import MongoDatabaseWrapper
from mdstudio.unittest import db
from mdstudio.unittest.db import DBTestCase


class TestMongoClientWrapper(DBTestCase):

    def setUp(self):
        self.d = MongoClientWrapper("localhost", 27127)

    def test_construction(self):

        self.assertEqual(self.d._host, "localhost")
        self.assertEqual(self.d._port, 27127)
        self.assertEqual(self.d._databases, {})
        self.assertIsInstance(self.d._client, mongomock.MongoClient)

    def test_get_database_not_exists(self):

        self.d.logger = mock.MagicMock()
        db = self.d.get_database('database_name')

        self.d.logger.info.assert_called_once_with('Creating database "{database}"', database='database_name')

        self.assertIsInstance(db, MongoDatabaseWrapper)
        self.assertEqual(db, self.d.get_database('database_name'))

    def test_get_database_exists(self):

        self.d._client.get_database('database_name')
        self.d.logger = mock.MagicMock()

        db = self.d.get_database('database_name')

        self.d.logger.info.assert_not_called()

        self.assertIsInstance(db, MongoDatabaseWrapper)
        self.assertEqual(db, self.d.get_database('database_name'))

    def test_create_mongo_client(self):
        db.create_mock_client = False

        self.assertIsInstance(MongoClientWrapper.create_mongo_client('localhost', 2), pymongo.MongoClient)

    def test_create_mongo_client_mock(self):
        db.create_mock_client = True

        self.assertIsInstance(MongoClientWrapper.create_mongo_client('localhost', 2), mongomock.MongoClient)
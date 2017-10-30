from mock import mock
import pymongo
import mongomock

from lie_db.db_methods import logger, MongoDatabaseWrapper
from lie_db.mongo_client_wrapper import MongoClientWrapper
from mdstudio.unittest import db
from mdstudio.unittest.db import DBTestCase


class TestMongoClientWrapper(DBTestCase):

    def setUp(self):
        self.d = MongoClientWrapper("localhost", 27127)

    def test_construction(self):

        self.assertEqual(self.d._host, "localhost")
        self.assertEqual(self.d._port, 27127)
        self.assertEqual(self.d._namespaces, {})
        self.assertIsInstance(self.d._client, mongomock.MongoClient)

    def test_get_namespace_not_exists(self):

        with mock.patch('lie_db.db_methods.logger.info'):

            db = self.d.get_namespace('ns1')

            logger.info.assert_called_once_with('Creating database for {namespace}', namespace='ns1')

            self.assertIsInstance(db, MongoDatabaseWrapper)
            self.assertEqual(db, self.d.get_namespace('ns1'))

    def test_get_namespace_exists(self):

        self.d._client.get_database('ns1')

        with mock.patch('lie_db.db_methods.logger.info'):

            db = self.d.get_namespace('ns1')

            logger.info.assert_not_called()

            self.assertIsInstance(db, MongoDatabaseWrapper)
            self.assertEqual(db, self.d.get_namespace('ns1'))

    def test_create_mongo_client(self):
        db.create_mock_client = False

        self.assertIsInstance(MongoClientWrapper.create_mongo_client('localhost', 2), pymongo.MongoClient)

    def test_create_mongo_client_mock(self):
        db.create_mock_client = True

        self.assertIsInstance(MongoClientWrapper.create_mongo_client('localhost', 2), mongomock.MongoClient)
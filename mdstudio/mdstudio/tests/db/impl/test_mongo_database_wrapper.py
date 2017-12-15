# coding=utf-8

import datetime

import mongomock
import pytz
import twisted
from bson import ObjectId
from faker import Faker
from mock import mock, call
from twisted.internet import reactor

from mdstudio.db.cursor import Cursor, query
from mdstudio.db.exception import DatabaseException
from mdstudio.db.fields import Fields
from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from mdstudio.service.model import Model
from mdstudio.db.sort_mode import SortMode
from mdstudio.deferred.chainable import test_chainable
from mdstudio.unittest.db import DBTestCase

twisted.internet.base.DelayedCall.debug = True


# noinspection PyUnresolvedReferences
class TestMongoDatabaseWrapper(DBTestCase):
    faker = Faker()

    def setUp(self):
        self.db = MongoClientWrapper("localhost", 27127).get_database('users~userNameDatabase')
        self.claims = {
            'connectionType': 'user',
            'username': 'userNameDatabase'
        }
        self.d = Model(self.db, 'test_collection')

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

    def test_prepare_sortmode_asc(self):
        sort = ('test', SortMode.Asc)

        sort = self.db._prepare_sortmode(sort)

        self.assertEqual(sort, [('test', 1)])

    def test_prepare_sortmode_desc(self):
        sort = ('test', SortMode.Desc)

        sort = self.db._prepare_sortmode(sort)

        self.assertEqual(sort, [('test', -1)])

    def test_prepare_sortmode_asc2(self):
        sort = ('test', "asc")

        sort = self.db._prepare_sortmode(sort)

        self.assertEqual(sort, [('test', 1)])

    def test_prepare_sortmode_desc2(self):
        sort = ('test', "desc")

        sort = self.db._prepare_sortmode(sort)

        self.assertEqual(sort, [('test', -1)])

    def test_prepare_sortmode_list(self):
        sort = [
            ('test', SortMode.Desc),
            ('test2', SortMode.Asc),
        ]

        sort = self.db._prepare_sortmode(sort)

        self.assertEqual(sort, [
            ('test', -1),
            ('test2', 1)
        ])

    def test_prepare_for_json(self):
        document = {
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                         datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        self.db._prepare_for_json(document)

        self.assertEqual(document, {
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                         datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_json_id(self):
        document = {
            '_id': 1000,
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                         datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        self.db._prepare_for_json(document)

        self.assertEqual(document, {
            '_id': '1000',
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                         datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_json_none(self):
        document = None

        self.db._prepare_for_json(document)

        self.assertEqual(document, None)

    def test_prepare_for_json_int(self):
        document = 2

        self.db._prepare_for_json(document)

        self.assertEqual(document, 2)

    def test_prepare_for_json_int_list(self):
        document = [2, 3, 4]

        self.db._prepare_for_json(document)

        self.assertEqual(document, [2, 3, 4])

    def test_prepare_for_mongo(self):
        document = {
            'o': {
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        result = self.db._prepare_for_mongo(document)

        self.assertIsNot(document, result)
        self.assertEqual(result, {
            'o': {
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_mongo_id(self):
        document = {
            '_id': '0123456789ab0123456789ab',
            'o': {
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        result = self.db._prepare_for_mongo(document)

        self.assertIsNot(document, result)
        self.assertEqual(result, {
            '_id': ObjectId('0123456789ab0123456789ab'),
            'o': {
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_mongo_none(self):
        document = None

        result = self.db._prepare_for_mongo(document)

        self.assertEqual(result, None)

    def test_get_collection_dict(self):

        self.db._logger = mock.MagicMock()
        collection = {
            'name': 'test_collection'
        }
        self.assertEqual(self.db._get_collection(collection), None)
        self.db._logger.info.assert_not_called()

    def test_get_collection_dict_create(self):

        self.db._logger = mock.MagicMock()
        collection = {
            'name': 'test_collection'
        }
        self.assertIsInstance(self.db._get_collection(collection, create=True), mongomock.collection.Collection)

        self.db._logger.info.assert_called_once_with('Creating collection {collection} in {database}',
                                                     collection='test_collection', database='users~userNameDatabase')

    def test_get_collection_str(self):

        self.db._logger = mock.MagicMock()
        collection = 'test_collection'
        self.assertEqual(self.db._get_collection(collection), None)
        self.db._logger.info.assert_not_called()

    def test_get_collection_str_create(self):

        self.db._logger = mock.MagicMock()
        collection = 'test_collection'
        self.assertIsInstance(self.db._get_collection(collection, create=True), mongomock.collection.Collection)

        self.db._logger.info.assert_called_once_with('Creating collection {collection} in {database}',
                                                     collection='test_collection', database='users~userNameDatabase')

    @test_chainable
    def test_insert_one(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        o = {'test': 2, '_id': '0123456789ab0123456789ab'}
        oid = yield self.d.insert_one(o)
        self.assertEqual(oid, '0123456789ab0123456789ab')
        self.db._prepare_for_mongo.assert_called_with(o)
        found = yield self.d.find_one({'_id': '0123456789ab0123456789ab'})

        self.assertEqual(found, {'test': 2, '_id': '0123456789ab0123456789ab'})

    @test_chainable
    def test_insert_one_not_modified(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        o = {'test': 2, '_id': '0123456789ab0123456789ab'}
        yield self.d.insert_one(o)
        found = yield self.d.find_one({'_id': '0123456789ab0123456789ab'})

        self.assertIsNot(o, found)

    @test_chainable
    def test_insert_one_no_id(self):

        oid = yield self.d.insert_one({'test': 2})
        found = yield self.d.find_one({'_id': oid})

        self.assertEqual(found, {'test': 2, '_id': oid})

    @test_chainable
    def test_insert_one_create_flag(self):
        self.db._get_collection = mock.MagicMock()

        yield self.d.insert_one({'test': 2})

        self.db._get_collection.assert_called_once_with('test_collection', True)

    @test_chainable
    def test_insert_one_date_time_fields(self):
        ldatetime = self.faker.date_time(pytz.utc)
        yield self.d.insert_one({'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': ldatetime},
                                fields=Fields(date_times=['datetime']))
        found = yield self.d.find_one({'_id': '0123456789ab0123456789ab'})

        self.assertEqual(found, {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': ldatetime})

    @test_chainable
    def test_insert_one_date_fields(self):
        date = self.faker.date_object()
        yield self.d.insert_one({'test': 2, '_id': '0123456789ab0123456789ab', 'date': date}, fields=Fields(dates=['date']))
        found = yield self.d.find_one({'_id': '0123456789ab0123456789ab'}, fields=Fields(dates=['date']))
        self.assertEqual(found, {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date})

    @test_chainable
    def test_insert_one_date_fields2(self):
        date = self.faker.date_object()
        stored = datetime.datetime.combine(date, datetime.time(hour=0, tzinfo=pytz.utc))
        yield self.d.insert_one({'test': 2, '_id': '0123456789ab0123456789ab', 'date': date}, fields=Fields(dates=['date']))
        found = yield self.d.find_one({'_id': '0123456789ab0123456789ab'})
        self.assertEqual(found, {'test': 2, '_id': '0123456789ab0123456789ab', 'date': stored})

    @test_chainable
    def test_insert_many(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = [
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ]
        ids = yield self.d.insert_many(obs)
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        self.db._prepare_for_mongo.assert_called_with(obs)

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 3, '_id': ids[1]})

    @test_chainable
    def test_insert_many_not_modified(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = [
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ]
        ids = yield self.d.insert_many(obs)
        found1 = yield self.d.find_one({'_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertIsNot(found1, obs[0])
        self.assertIsNot(found2, obs[1])

    @test_chainable
    def test_insert_many_no_ids(self):

        ids = yield self.d.insert_many([
            {'test': 2},
            {'test': 3}
        ])
        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 3, '_id': ids[1]})

    @test_chainable
    def test_insert_many_create_flag(self):
        self.db._get_collection = mock.MagicMock()

        yield self.d.insert_many([
            {'test': 2},
            {'test': 3}
        ], fields=Fields(date_times=['date']))

        self.db._get_collection.assert_called_once_with('test_collection', True)

    @test_chainable
    def test_insert_many_date_time_fields(self):
        ldatetime = self.faker.date_time(pytz.utc)
        yield self.d.insert_many([{'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': ldatetime}],
                                 fields=Fields(date_times=['datetime']))
        found = yield self.d.find_many({'_id': '0123456789ab0123456789ab'}).to_list()

        self.assertEqual(found[0], {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': ldatetime})

    @test_chainable
    def test_insert_many_date_fields(self):
        date = self.faker.date_object()
        yield self.d.insert_many([{'test': 2, '_id': '0123456789ab0123456789ab', 'date': date}], fields=Fields(dates=['date']))
        found = yield self.d.find_many({'_id': '0123456789ab0123456789ab'}, fields=Fields(dates=['date'])).to_list()
        self.assertEqual(found[0], {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date})

    @test_chainable
    def test_insert_many_date_fields2(self):
        date = self.faker.date_object()
        stored = datetime.datetime.combine(date, datetime.time(hour=0, tzinfo=pytz.utc))
        yield self.d.insert_many([{'test': 2, '_id': '0123456789ab0123456789ab', 'date': date}], fields=Fields(dates=['date']))
        found = yield self.d.find_many({'_id': '0123456789ab0123456789ab'}).to_list()
        self.assertEqual(found[0], {'test': 2, '_id': '0123456789ab0123456789ab', 'date': stored})

    @test_chainable
    def test_replace_one(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = [
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ]
        ids = yield self.d.insert_many(obs)
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        result = yield self.d.replace_one({'_id': '59f1d9c57dd5d70043e74f8d'}, {'test2': 6})

        self.db._get_collection.assert_called_once_with('test_collection', False)
        self.db._prepare_for_mongo.assert_has_calls(
            [call(obs), call({'_id': '59f1d9c57dd5d70043e74f8d'}), call({'test2': 6})])

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test2': 6, '_id': ids[1]})

        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

    @test_chainable
    def test_replace_one_upsert(self):

        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ])
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        result = yield self.d.replace_one({'_id': '666f6f2d6261722d71757578'}, {'test': 6}, upsert=True)

        self.db._get_collection.assert_called_once_with('test_collection', True)

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 3, '_id': ids[1]})
        found3 = yield self.d.find_one({'_id': '666f6f2d6261722d71757578'})
        self.assertEqual(found3, {'test': 6, '_id': '666f6f2d6261722d71757578'})

        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 0)
        self.assertEqual(result.upserted_id, '666f6f2d6261722d71757578')

    @test_chainable
    def test_replace_one_no_collection(self):

        result = yield self.d.replace_one({'_id': '666f6f2d6261722d71757578'}, {'test': 6})

        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 0)
        self.assertEqual(result.upserted_id, None)

    @test_chainable
    def test_replace_one_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.replace_one({'_id': '59f1d9c57dd5d70043e74f8d'}, {'test': 6, 'datetime': datetime}, fields=Fields(date_times=['date']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'test': 6, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime})

    @test_chainable
    def test_replace_one_date_fields(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.replace_one({'_id': '59f1d9c57dd5d70043e74f8d'}, {'test': 6, 'date': date}, fields=Fields(dates=['date']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date']))
        self.assertEqual(found, {'test': 6, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date})

    @test_chainable
    def test_replace_one_date_fields2(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        stored = datetime.datetime.combine(date, datetime.time(hour=0, tzinfo=pytz.utc))
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.replace_one({'_id': '59f1d9c57dd5d70043e74f8d'}, {'test': 6, 'date': date})

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'test': 6, '_id': '59f1d9c57dd5d70043e74f8d', 'date': stored})

    @test_chainable
    def test_update_one(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = [
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ]
        ids = yield self.d.insert_many(obs)
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        result = yield self.d.update_one({'_id': '59f1d9c57dd5d70043e74f8d'}, {'$set': {'test': 6}})

        self.db._get_collection.assert_called_once_with('test_collection', False)
        self.db._prepare_for_mongo.assert_has_calls(
            [call(obs), call({'_id': '59f1d9c57dd5d70043e74f8d'}), call({'$set': {'test': 6}})])

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 6, '_id': ids[1]})

        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

    @test_chainable
    def test_update_one_functionality(self):

        obs = [
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 2, '_id': '59f1d9c57dd5d70043e74f8d'},
            {'test': 6, '_id': '666f6f2d6261722d71757578'}
        ]
        ids = yield self.d.insert_many(obs)

        result = yield self.d.update_one({'test': 2}, {'$set': {'test2': 6}})

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, 'test2': 6, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 2, '_id': ids[1]})
        found3 = yield self.d.find_one({'_id': ids[2]})
        self.assertEqual(found3, {'test': 6, '_id': ids[2]})

        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

    @test_chainable
    def test_update_one_upsert(self):

        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ])
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        result = yield self.d.update_one({'_id': '666f6f2d6261722d71757578'}, {'$set': {'test': 6}}, upsert=True)

        self.db._get_collection.assert_called_once_with('test_collection', True)

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 3, '_id': ids[1]})
        found3 = yield self.d.find_one({'_id': '666f6f2d6261722d71757578'})
        self.assertEqual(found3, {'test': 6, '_id': '666f6f2d6261722d71757578'})

        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 0)
        self.assertEqual(result.upserted_id, '666f6f2d6261722d71757578')

    @test_chainable
    def test_update_one_no_collection(self):

        result = yield self.d.update_one({'_id': '666f6f2d6261722d71757578'}, {'$set': {'test': 6}})

        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 0)
        self.assertEqual(result.upserted_id, None)

    @test_chainable
    def test_update_one_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.update_one({'_id': '59f1d9c57dd5d70043e74f8d'}, {'$set': {'test': 6}}, fields=Fields(date_times=['date']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'test': 6, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2})

    @test_chainable
    def test_update_one_date_fields(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.update_one({'_id': '59f1d9c57dd5d70043e74f8d'}, {'$set': {'test': 6}}, fields=Fields(dates=['date']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date']))
        self.assertEqual(found, {'test': 6, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2})

    @test_chainable
    def test_update_one_date_fields2(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        stored = datetime.datetime.combine(date2, datetime.time(hour=0, tzinfo=pytz.utc))
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.update_one({'_id': '59f1d9c57dd5d70043e74f8d'}, {'$set': {'test': 6}}, fields=Fields(dates=['date']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'test': 6, '_id': '59f1d9c57dd5d70043e74f8d', 'date': stored})

    @test_chainable
    def test_update_many(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = [
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ]
        ids = yield self.d.insert_many(obs)
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        result = yield self.d.update_many({'_id': '59f1d9c57dd5d70043e74f8d'}, {'$set': {'test': 6}})

        self.db._get_collection.assert_called_once_with('test_collection', False)
        self.db._prepare_for_mongo.assert_has_calls(
            [call(obs), call({'_id': '59f1d9c57dd5d70043e74f8d'}), call({'$set': {'test': 6}})])

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 6, '_id': ids[1]})

        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

    @test_chainable
    def test_update_many_functionality(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = [
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 2, '_id': '59f1d9c57dd5d70043e74f8d'},
            {'test': 6, '_id': '666f6f2d6261722d71757578'}
        ]
        ids = yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        result = yield self.d.update_many({'test': 2}, {'$set': {'test2': 6}})

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, 'test2': 6, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 2, 'test2': 6, '_id': ids[1]})
        found3 = yield self.d.find_one({'_id': ids[2]})
        self.assertEqual(found3, {'test': 6, '_id': ids[2]})

        self.assertEqual(result.matched, 2)
        self.assertEqual(result.modified, 2)
        self.assertEqual(result.upserted_id, None)

    @test_chainable
    def test_update_many_upsert(self):

        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ])
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        result = yield self.d.update_many({'_id': '666f6f2d6261722d71757578'}, {'$set': {'test': 6}}, upsert=True)

        self.db._get_collection.assert_called_once_with('test_collection', True)

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 3, '_id': ids[1]})
        found3 = yield self.d.find_one({'_id': '666f6f2d6261722d71757578'})
        self.assertEqual(found3, {'test': 6, '_id': '666f6f2d6261722d71757578'})

        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 0)
        self.assertEqual(result.upserted_id, '666f6f2d6261722d71757578')

    @test_chainable
    def test_update_many_no_collection(self):

        result = yield self.d.update_many({'_id': '666f6f2d6261722d71757578'}, {'$set': {'test': 6}})

        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 0)
        self.assertEqual(result.upserted_id, None)

    @test_chainable
    def test_update_many_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.update_many({'_id': '59f1d9c57dd5d70043e74f8d'}, {'$set': {'test': 6}}, fields=Fields(date_times=['date']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'test': 6, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2})

    @test_chainable
    def test_update_many_date_fields(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.update_many({'_id': '59f1d9c57dd5d70043e74f8d'}, {'$set': {'test': 6}}, fields=Fields(dates=['date']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date']))
        self.assertEqual(found, {'test': 6, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2})

    @test_chainable
    def test_update_many_date_fields2(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        stored = datetime.datetime.combine(date2, datetime.time(hour=0, tzinfo=pytz.utc))
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.update_many({'_id': '59f1d9c57dd5d70043e74f8d'}, {'$set': {'test': 6}}, fields=Fields(dates=['date']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'test': 6, '_id': '59f1d9c57dd5d70043e74f8d', 'date': stored})

    @test_chainable
    def test_find_one(self):

        total = 100
        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one({'test': i})
            self.db._get_collection.assert_called_once_with('test_collection')

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

    @test_chainable
    def test_find_one_projection(self):

        total = 100
        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        for i in range(total):
            found = yield self.d.find_one({'test': i}, {'_id': 0})
            self.assertEqual(found, {'test': i})

    @test_chainable
    def test_find_one_skip(self):

        total = 100
        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(total):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(total):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            found = yield self.d.find_one({'test': i}, skip=1, sort=('_id', SortMode.Asc))
            self.assertEqual(obs[i + total]['_id'], ids[i + total])
            self.assertEqual(found, obs[i + total])

    @test_chainable
    def test_find_one_sort(self):

        total = 100
        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(total):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(total):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            found = yield self.d.find_one({'test': i}, sort=('_id', SortMode.Desc))
            self.assertEqual(obs[i + total]['_id'], ids[i + total])
            self.assertEqual(found, obs[i + total])

        for i in range(total):
            found = yield self.d.find_one({'test': i}, sort=('_id', SortMode.Asc))
            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

    @test_chainable
    def test_find_one_no_collection(self):

        result = yield self.d.find_one({'_id': '666f6f2d6261722d71757578'})

        self.assertEqual(result, None)

    @test_chainable
    def test_find_one_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['datetime']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2})

    @test_chainable
    def test_find_one_date_fields(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date']))
        self.assertEqual(found, {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2})

    @test_chainable
    def test_find_one_date_fields2(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        stored = datetime.datetime.combine(date2, datetime.time(hour=0, tzinfo=pytz.utc))
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': stored})

    @test_chainable
    def test_find_many(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.find_many({})
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertIsInstance(found, Cursor)
        self.assertSequenceEqual((yield found.to_list()), obs)

    @test_chainable
    def test_find_many_parse_result(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        fields = Fields()
        fields.parse_result = mock.MagicMock(wraps=fields.parse_result)
        yield self.db.find_many('test_collection', {}, fields=fields, claims={'user': 'test'})

        fields.parse_result.assert_has_calls([])

    @test_chainable
    def test_find_many_projection(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        found = yield self.d.find_many({}, {'_id': 0})

        self.assertIsInstance(found, Cursor)
        self.assertSequenceEqual((yield found.to_list()), query(obs).select(lambda x: {'test': x['test']}).to_list())

    @test_chainable
    def test_find_many_skip(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        found = yield self.d.find_many({}, skip=10)

        self.assertIsInstance(found, Cursor)
        self.assertSequenceEqual((yield found.to_list()), obs[10:])

    @test_chainable
    def test_find_many_limit(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        found = yield self.d.find_many({}, limit=10)

        self.assertIsInstance(found, Cursor)
        self.assertSequenceEqual((yield found.to_list()), obs[:10])

    @test_chainable
    def test_find_many_sort(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        found = yield self.d.find_many({}, sort=('test', SortMode.Desc))

        self.assertIsInstance(found, Cursor)
        self.assertListEqual((yield found.to_list()), list(reversed(obs)))

    @test_chainable
    def test_find_many_no_collection(self):

        result = yield self.d.find_many({'_id': '666f6f2d6261722d71757578'})

        self.assertIsInstance(result, Cursor)
        self.assertSequenceEqual((yield result.to_list()), [])

    @test_chainable
    def test_find_many_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['datetime']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        found = yield self.d.find_many({'_id': '59f1d9c57dd5d70043e74f8d'}).to_list()
        self.assertEqual(found[0], {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2})

    @test_chainable
    def test_find_many_date_fields(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        found = yield self.d.find_many({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date'])).to_list()
        self.assertEqual(found[0], {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2})

    @test_chainable
    def test_find_many_date_fields2(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        stored = datetime.datetime.combine(date2, datetime.time(hour=0, tzinfo=pytz.utc))
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        found = yield self.d.find_many({'_id': '59f1d9c57dd5d70043e74f8d'}).to_list()
        self.assertEqual(found[0], {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': stored})

    @test_chainable
    def test_more_dry(self):
        d = self.d.wrapper.more("wefwefwef")
        yield self.assertFailure(d, DatabaseException)

    @test_chainable
    def test_rewind(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.find_many({})
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertIsInstance(found, Cursor)

        for i in range(total):
            self.assertEqual((yield next(found)), obs[i])

        yield found.rewind()

        for i in range(total):
            self.assertEqual((yield next(found)), obs[i])

    @test_chainable
    def test_rewind_dry(self):
        yield self.assertFailure(self.d.wrapper.rewind("wefwefwef"), DatabaseException)

    @test_chainable
    def test_count_cursor(self):

        total = 200
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.find_many({})
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertIsInstance(found, Cursor)
        self.assertEqual((yield found.count()), 200)

    @test_chainable
    def test_count_no_filter(self):

        total = 200
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        count = yield self.d.count()
        self.db._get_collection.assert_called_once_with('test_collection')
        self.assertEqual(count, 200)

    @test_chainable
    def test_count_filter(self):

        total = 200
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        count = yield self.d.count({'test': {'$gt': 50}})
        self.db._get_collection.assert_called_once_with('test_collection')
        self.assertEqual(count, 149)

    @test_chainable
    def test_count_filter_skip(self):

        total = 200
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        count = yield self.d.count({'test': {'$lt': 50}}, skip=10)
        self.db._get_collection.assert_called_once_with('test_collection')
        self.assertEqual(count, 40)

    @test_chainable
    def test_count_filter_limit(self):

        total = 200
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        count = yield self.d.count({'test': {'$gt': 50}}, limit=10)
        self.db._get_collection.assert_called_once_with('test_collection')
        self.assertEqual(count, 10)

    @test_chainable
    def test_count_filter_no_collection(self):

        result = yield self.d.count({'_id': '666f6f2d6261722d71757578'})

        self.assertEqual(result, 0)

    @test_chainable
    def test_count_neither(self):

        result = yield self.d.count()
        self.assertEqual(result, 0)

    @test_chainable
    def test_count_filter_date_time_fields(self):

        total = 200
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId()), 'datetime': self.faker.date_time(pytz.utc)})
        yield self.d.insert_many(obs, fields=Fields(date_times=['datetime']))

        yield self.d.count({'test': {'$gt': 50}}, fields=Fields(date_times=['datetime']))

    @test_chainable
    def test_count_filter_date_fields(self):

        total = 200
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId()), 'date': self.faker.date_time(pytz.utc)})
        yield self.d.insert_many(obs, fields=Fields(dates=['date']))

        yield self.d.count({'test': {'$gt': 50}}, fields=Fields(dates=['date']))

    @test_chainable
    def test_find_one_and_update(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_update({'test': i}, {'$set': {'test2': total - i}})
            self.db._get_collection.assert_called_once_with('test_collection', False)

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

            found2 = yield self.d.find_one({'test': i})
            self.assertEqual(found2, {'_id': obs[i]['_id'], 'test': i, 'test2': total - i})

    @test_chainable
    def test_find_one_and_update_upsert(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_update({'test': i}, {'$set': {'test2': total - i}}, upsert=True)
            self.db._get_collection.assert_called_once_with('test_collection', True)

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

            found2 = yield self.d.find_one({'test': i})
            self.assertEqual(found2, {'_id': obs[i]['_id'], 'test': i, 'test2': total - i})

    @test_chainable
    def test_find_one_and_update_upsert2(self):

        total = 100
        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_update({'test': i}, {'$set': {'test2': total - i}}, upsert=True)
            self.db._get_collection.assert_called_once_with('test_collection', True)

            found2 = yield self.d.find_one({'test': i})

            self.assertEqual(found, None)
            self.assertEqual(found2['test'], i)
            self.assertEqual(found2['test2'], total - i)

    @test_chainable
    def test_find_one_and_update_projection(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_update({'test': i}, {'$set': {'test2': total - i}}, projection={'_id': 0})
            self.db._get_collection.assert_called_once_with('test_collection', False)

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, {'test': i})

            found2 = yield self.d.find_one({'test': i})
            self.assertEqual(found2, {'_id': obs[i]['_id'], 'test': i, 'test2': total - i})

    @test_chainable
    def test_find_one_and_update_sort(self):

        total = 100
        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(total):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(total):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            found = yield self.d.find_one_and_update({'test': i}, {'$set': {'test2': total - i}},
                                                     sort=('_id', SortMode.Desc))
            self.assertEqual(obs[i + total]['_id'], ids[i + total])
            self.assertEqual(found, obs[i + total])

        for i in range(total):
            found = yield self.d.find_one_and_update({'test': i}, {'$set': {'test2': total - i}},
                                                     sort=('_id', SortMode.Asc))
            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

    @test_chainable
    def test_find_one_and_update_return_updated(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_update({'test': i}, {'$set': {'test2': total - i}}, return_updated=True)
            self.db._get_collection.assert_called_once_with('test_collection', False)

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, {'_id': obs[i]['_id'], 'test': i, 'test2': total - i})

    @test_chainable
    def test_find_one_and_update_collection(self):

        obs = [{'test': 1, '_id': str(ObjectId())}]
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        yield self.d.find_one_and_update({'test': 1}, {'$set': {'test2': 0}})
        self.db._get_collection.assert_called_once_with('test_collection', False)

    @test_chainable
    def test_find_one_and_update_no_collection(self):

        result = yield self.d.find_one_and_update({'_id': '666f6f2d6261722d71757578'}, {'$set': {'test': 6}})

        self.assertEqual(result, None)

    @test_chainable
    def test_find_one_and_update_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['datetime']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.find_one_and_update({'_id': '59f1d9c57dd5d70043e74f8d'}, {
            '$set': {'datetime2': datetime}
        }, fields=Fields(date_times=['datetime']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(date_times=['datetime', 'datetime2']))
        self.assertEqual(found, {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2, 'datetime2': datetime})

    @test_chainable
    def test_find_one_and_update_date_fields(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.find_one_and_update({'_id': '59f1d9c57dd5d70043e74f8d'}, {
            '$set': {'date2': date}
        }, fields=Fields(dates=['date2']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date', 'date2']))
        self.assertEqual(found, {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2, 'date2': date})

    @test_chainable
    def test_find_one_and_update_date_fields2(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        stored = datetime.datetime.combine(date, datetime.time(hour=0, tzinfo=pytz.utc))
        stored2 = datetime.datetime.combine(date2, datetime.time(hour=0, tzinfo=pytz.utc))
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))

        yield self.d.find_one_and_update({'_id': '59f1d9c57dd5d70043e74f8d'}, {
            '$set': {'date2': date}
        }, fields=Fields(dates=['date2']))

        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': stored2, 'date2': stored})

    @test_chainable
    def test_find_one_and_replace(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_replace({'test': i}, {'test2': total - i})
            self.db._get_collection.assert_called_once_with('test_collection', False)

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

            found2 = yield self.d.find_one({'test': i})
            found3 = yield self.d.find_one({'test2': total - i})
            self.assertEqual(found2, None)
            self.assertEqual(found3, {'_id': obs[i]['_id'], 'test2': total - i})

    @test_chainable
    def test_find_one_and_replace_upsert(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_replace({'test': i}, {'test2': total - i}, upsert=True)
            self.db._get_collection.assert_called_once_with('test_collection', True)

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

            found2 = yield self.d.find_one({'test': i})
            found3 = yield self.d.find_one({'test2': total - i})
            self.assertEqual(found2, None)
            self.assertEqual(found3, {'_id': obs[i]['_id'], 'test2': total - i})

    @test_chainable
    def test_find_one_and_replace_upsert2(self):

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.find_one_and_replace({'test': 0}, {'test2': 100}, upsert=True)
        self.db._get_collection.assert_called_once_with('test_collection', True)

        found2 = yield self.d.find_one({'test': 0})
        found3 = yield self.d.find_one({'test2': 100})

        self.assertEqual(found, None)
        self.assertEqual(found2, None)
        self.assertEqual(found3['test2'], 100)

    @test_chainable
    def test_find_one_and_replace_upsert3(self):

        total = 100
        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_replace({'test': i}, {'test2': total - i}, upsert=True)
            self.db._get_collection.assert_called_once_with('test_collection', True)

            found2 = yield self.d.find_one({'test': i})
            found3 = yield self.d.find_one({'test2': total - i})

            self.assertEqual(found, None)
            self.assertEqual(found2, None)
            self.assertEqual(found3['test2'], total - i)

    @test_chainable
    def test_find_one_and_replace_projection(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_replace({'test': i}, {'test2': total - i}, projection={'_id': 0})
            self.db._get_collection.assert_called_once_with('test_collection', False)

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, {'test': i})

            found2 = yield self.d.find_one({'test': i})
            found3 = yield self.d.find_one({'test2': total - i})
            self.assertEqual(found2, None)
            self.assertEqual(found3, {'_id': obs[i]['_id'], 'test2': total - i})

    @test_chainable
    def test_find_one_and_replace_sort(self):

        total = 100
        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(total):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(total):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            found = yield self.d.find_one_and_replace({'test': i}, {'test2': total - i}, sort=('_id', SortMode.Desc))
            self.assertEqual(obs[i + total]['_id'], ids[i + total])
            self.assertEqual(found, obs[i + total])

        for i in range(total):
            found = yield self.d.find_one_and_replace({'test': i}, {'test2': total - i}, sort=('_id', SortMode.Asc))
            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

    @test_chainable
    def test_find_one_and_replace_return_updated(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_replace({'test': i}, {'test2': total - i}, return_updated=True)
            self.db._get_collection.assert_called_once_with('test_collection', False)

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, {'_id': obs[i]['_id'], 'test2': total - i})

    @test_chainable
    def test_find_one_and_replace_collection(self):

        obs = [{'test': 1, '_id': str(ObjectId())}]
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        yield self.d.find_one_and_replace({'test': 1}, {'test2': 0})
        self.db._get_collection.assert_called_once_with('test_collection', False)

    @test_chainable
    def test_find_one_and_replace_no_collection(self):

        result = yield self.d.find_one_and_replace({'_id': '666f6f2d6261722d71757578'}, {'test': 6})

        self.assertEqual(result, None)

    @test_chainable
    def test_find_one_and_replace_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['datetime']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.find_one_and_replace({'_id': '59f1d9c57dd5d70043e74f8d'}, {'datetime2': datetime},
                                          fields=Fields(date_times=['datetime']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(date_times=['datetime', 'datetime2']))
        self.assertEqual(found, {'_id': '59f1d9c57dd5d70043e74f8d', 'datetime2': datetime})

    @test_chainable
    def test_find_one_and_replace_date_fields(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.find_one_and_replace({'_id': '59f1d9c57dd5d70043e74f8d'}, {'date2': date}, fields=Fields(dates=['date2']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date', 'date2']))
        self.assertEqual(found, {'_id': '59f1d9c57dd5d70043e74f8d', 'date2': date})

    @test_chainable
    def test_find_one_and_replace_date_fields2(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        stored = datetime.datetime.combine(date, datetime.time(hour=0, tzinfo=pytz.utc))
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))

        yield self.d.find_one_and_replace({'_id': '59f1d9c57dd5d70043e74f8d'}, {'date2': date}, fields=Fields(dates=['date2']))

        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, {'_id': '59f1d9c57dd5d70043e74f8d', 'date2': stored})

    @test_chainable
    def test_find_one_and_delete(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_delete({'test': i})
            self.db._get_collection.assert_called_once_with('test_collection')

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

            found2 = yield self.d.find_one({'test': i})
            self.assertEqual(found2, None)

    @test_chainable
    def test_find_one_and_delete_projection(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
            found = yield self.d.find_one_and_delete({'test': i}, projection={'_id': 0})
            self.db._get_collection.assert_called_once_with('test_collection')

            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, {'test': i})

            found2 = yield self.d.find_one({'test': i})
            self.assertEqual(found2, None)

    @test_chainable
    def test_find_one_and_delete_sort(self):

        total = 100
        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(total):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(total):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(total):
            found = yield self.d.find_one_and_delete({'test': i}, sort=('_id', SortMode.Desc))
            self.assertEqual(obs[i + total]['_id'], ids[i + total])
            self.assertEqual(found, obs[i + total])

        for i in range(total):
            found = yield self.d.find_one_and_delete({'test': i}, sort=('_id', SortMode.Asc))
            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

    @test_chainable
    def test_find_one_and_delete_collection(self):

        obs = [{'test': 1, '_id': str(ObjectId())}]
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        yield self.d.find_one_and_delete({'test': 1}, {'test2': 0})
        self.db._get_collection.assert_called_once_with('test_collection')

    @test_chainable
    def test_find_one_and_delete_no_collection(self):

        result = yield self.d.find_one_and_delete({'_id': '666f6f2d6261722d71757578'}, {'test': 6})

        self.assertEqual(result, None)

    @test_chainable
    def test_find_one_and_delete_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['datetime']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.find_one_and_delete({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(date_times=['datetime']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(date_times=['datetime', 'datetime2']))
        self.assertEqual(found, None)

    @test_chainable
    def test_find_one_and_delete_date_fields(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.find_one_and_delete({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date2']))

        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date', 'date2']))
        self.assertEqual(found, None)

    @test_chainable
    def test_find_one_and_delete_date_fields2(self):
        date = self.faker.date_object()
        date2 = self.faker.date_object()
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'date': date},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'date': date2},
        ], fields=Fields(dates=['date']))

        yield self.d.find_one_and_delete({'_id': '59f1d9c57dd5d70043e74f8d'}, fields=Fields(dates=['date2']))

        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])
        found = yield self.d.find_one({'_id': '59f1d9c57dd5d70043e74f8d'})
        self.assertEqual(found, None)

    @test_chainable
    def test_distinct(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.distinct('test')
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertEqual(found, list(range(total)))

    @test_chainable
    def test_distinct2(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.distinct('test')
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertEqual(found, list(range(total)))

    @test_chainable
    def test_distinct_filter(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.distinct('test', {'test': {'$gt': 50}})
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertEqual(found, list(range(51, total)))

    @test_chainable
    def test_distinct_collection(self):

        obs = [{'test': 1, '_id': str(ObjectId())}]
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        yield self.d.distinct('test')
        self.db._get_collection.assert_called_once_with('test_collection')

    @test_chainable
    def test_distinct_no_collection(self):

        result = yield self.d.distinct('test')

        self.assertEqual(result, [])

    @test_chainable
    def test_distinct_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['datetime']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.distinct('test', fields=Fields(date_times=['datetime']))

    @test_chainable
    def test_aggregate(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(total * 2):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.aggregate([
            {
                '$match': {'test': {'$gt': 50}}
            },
            {
                '$group': {
                    '_id': '$test2',
                    'count': {'$sum': 1}
                }
            }
        ])
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertIsInstance(found, Cursor)
        found_list = yield found.to_list()
        self.assertEqual(found_list[0], {'_id': '0', 'count': 49})
        self.assertEqual(found_list[1], {'_id': '1', 'count': 149})

    @test_chainable
    def test_aggregate2(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(total * 2):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.aggregate([
            {
                '$match': {'test': {'$gt': 50}}
            },
            {
                '$group': {
                    '_id': '$test',
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {
                    '_id': int(SortMode.Asc)
                }
            }
        ])
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertIsInstance(found, Cursor)
        found_list = yield found.to_list()
        for i in range(total * 2 - 51):
            self.assertEqual(found_list[i], {'_id': str(51 + i), 'count': 1 if i >= 49 else 2})

    @test_chainable
    def test_aggregate_no_collection(self):

        result = yield self.d.aggregate([])

        self.assertSequenceEqual((yield result.to_list()), [])

    @test_chainable
    def test_delete_one(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(total):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        count = yield self.d.delete_one({'test': 1})
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertEqual(count, 1)
        found = yield self.d.find_one({'test': 1})
        self.assertEqual(found['test'], 1)
        self.assertEqual(found['test2'], 1)

    @test_chainable
    def test_delete_one_no_collection(self):

        result = yield self.d.delete_one({})

        self.assertEqual(result, 0)

    @test_chainable
    def test_delete_one_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['datetime']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.delete_one({'datetime': datetime}, fields=Fields(date_times=['datetime']))

    @test_chainable
    def test_delete_many(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(total):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        count = yield self.d.delete_many({'test': 1})
        self.db._get_collection.assert_called_once_with('test_collection')

        self.assertEqual(count, 2)
        found = yield self.d.find_one({'test': 1})
        self.assertEqual(found, None)

    @test_chainable
    def test_delete_many_no_collection(self):

        result = yield self.d.delete_many({})

        self.assertEqual(result, 0)

    @test_chainable
    def test_delete_many_date_time_fields(self):
        datetime = self.faker.date_time(pytz.utc)
        datetime2 = self.faker.date_time(pytz.utc)
        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab', 'datetime': datetime},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d', 'datetime': datetime2},
        ], fields=Fields(date_times=['datetime']))
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        yield self.d.delete_many({'datetime': datetime}, fields=Fields(date_times=['datetime']))

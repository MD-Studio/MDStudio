# coding=utf-8

import datetime

import mongomock
import pytz
import twisted
from bson import ObjectId
from copy import deepcopy
from mock import mock, call
from twisted.internet import reactor

from mdstudio.db.exception import DatabaseException
from mdstudio.db.fields import Fields
from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from mdstudio.db.cursor import Cursor, query
from mdstudio.db.model import Model
from mdstudio.db.sort_mode import SortMode
from mdstudio.deferred.chainable import chainable
from mdstudio.unittest import wait_for_completion
from mdstudio.unittest.db import DBTestCase

twisted.internet.base.DelayedCall.debug = True

class TestMongoDatabaseWrapper(DBTestCase):
    def setUp(self):
        self.db = MongoClientWrapper("localhost", 27127).get_database('users~userNameDatabase')
        self.claims = {
            'connectionType': 'user',
            'username': 'userNameDatabase'
        }
        self.d = Model(self.db, 'test_collection')

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

        wait_for_completion.wait_for_completion = True

    def tearDown(self):
        wait_for_completion.wait_for_completion = False

    def test_prepare_sortmode_asc(self):
        sort = ('test', SortMode.Asc)

        sort = self.db._prepare_sortmode(sort)

        self.assertEqual(sort, [('test', 1)])

    def test_prepare_sortmode_desc(self):
        sort = ('test', SortMode.Desc)

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

        # @todo
        #with mock.patch('mdstudio.db.mongo_client_wrapper.logger.info'):
            collection = {
                'name': 'test_collection'
            }
            self.assertEqual(self.db._get_collection(collection), None)
            #logger.info.assert_not_called()

    def test_get_collection_dict_create(self):

        # @todo
        #with mock.patch('mdstudio.db.mongo_client_wrapper.logger.info'):
            collection = {
                'name': 'test_collection'
            }
            self.assertIsInstance(self.db._get_collection(collection, create=True), mongomock.collection.Collection)

            #logger.info.assert_called_once_with('Creating collection {collection} in {database}',
            #                                    collection='test_collection', database='users~userNameDatabase')

    def test_get_collection_str(self):

        # @todo
        #with mock.patch('mdstudio.db.mongo_client_wrapper.logger.info'):
            collection = 'test_collection'
            self.assertEqual(self.db._get_collection(collection), None)
            #logger.info.assert_not_called()

    def test_get_collection_str_create(self):

        # @todo
        #with mock.patch('mdstudio.db.mongo_client_wrapper.logger.info'):
            collection = 'test_collection'
            self.assertIsInstance(self.db._get_collection(collection, create=True), mongomock.collection.Collection)

            #logger.info.assert_called_once_with('Creating collection {collection} in {database}',
            #                                    collection='test_collection', database='users~userNameDatabase')

    @chainable
    def test_insert_one(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        o = {'test': 2, '_id': '0123456789ab0123456789ab'}
        id = yield self.d.insert_one(o)
        self.assertEqual(id, '0123456789ab0123456789ab')
        self.db._prepare_for_mongo.assert_called_with(o)
        found = yield self.d.find_one({'_id': '0123456789ab0123456789ab'})

        self.assertEqual(found, {'test': 2, '_id': '0123456789ab0123456789ab'})

    @chainable
    def test_insert_one_not_modified(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        o = {'test': 2, '_id': '0123456789ab0123456789ab'}
        yield self.d.insert_one(o)
        found = yield self.d.find_one({'_id': '0123456789ab0123456789ab'})

        self.assertIsNot(o, found)

    @chainable
    def test_insert_one_no_id(self):

        id = yield self.d.insert_one({'test': 2})
        found = yield self.d.find_one({'_id': id})

        self.assertEqual(found, {'test': 2, '_id': id})

    @chainable
    def test_insert_one_create_flag(self):
        self.db._get_collection = mock.MagicMock()

        yield self.d.insert_one({'test': 2})

        self.db._get_collection.assert_called_once_with('test_collection', True)

    @chainable
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

    @chainable
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

    @chainable
    def test_insert_many_no_ids(self):

        ids = yield self.d.insert_many([
            {'test': 2},
            {'test': 3}
        ])
        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 3, '_id': ids[1]})

    @chainable
    def test_insert_many_create_flag(self):
        self.db._get_collection = mock.MagicMock()

        yield self.d.insert_many([
            {'test': 2},
            {'test': 3}
        ], fields=Fields(date_times=['date']))

        self.db._get_collection.assert_called_once_with('test_collection', True)

    @chainable
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

    @chainable
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

    @chainable
    def test_replace_one_no_collection(self):

        result = yield self.d.replace_one({'_id': '666f6f2d6261722d71757578'}, {'test': 6})

        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 0)
        self.assertEqual(result.upserted_id, None)

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
    def test_update_one_no_collection(self):

        result = yield self.d.update_one({'_id': '666f6f2d6261722d71757578'}, {'$set': {'test': 6}})

        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 0)
        self.assertEqual(result.upserted_id, None)

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
    def test_update_many_no_collection(self):

        result = yield self.d.update_many({'_id': '666f6f2d6261722d71757578'}, {'$set': {'test': 6}})

        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 0)
        self.assertEqual(result.upserted_id, None)

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
    def test_find_one_no_collection(self):

        result = yield self.d.find_one({'_id': '666f6f2d6261722d71757578'})

        self.assertEqual(result, None)

    @chainable
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

    @chainable
    def test_find_many_projection(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        found = yield self.d.find_many({}, {'_id': 0})

        self.assertIsInstance(found, Cursor)
        self.assertSequenceEqual((yield found.to_list()), query(obs).select(lambda x: {'test': x['test']}).to_list())

    @chainable
    def test_find_many_skip(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        found = yield self.d.find_many({}, skip=10)

        self.assertIsInstance(found, Cursor)
        self.assertSequenceEqual((yield found.to_list()), obs[10:])

    @chainable
    def test_find_many_limit(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        found = yield self.d.find_many({}, limit=10)

        self.assertIsInstance(found, Cursor)
        self.assertSequenceEqual((yield found.to_list()), obs[:10])

    @chainable
    def test_find_many_sort(self):

        total = 100
        obs = []
        for i in range(total):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        found = yield self.d.find_many({}, sort=('test', SortMode.Desc))

        self.assertIsInstance(found, Cursor)
        self.assertListEqual((yield found.to_list()), list(reversed(obs)))

    @chainable
    def test_find_many_no_collection(self):

        result = yield self.d.find_many({'_id': '666f6f2d6261722d71757578'})

        self.assertIsInstance(result, Cursor)
        self.assertSequenceEqual((yield result.to_list()), [])

    def test_more_dry(self):
        return self.assertFailure(self.d.wrapper.more("wefwefwef"), DatabaseException)

    @chainable
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

        found.rewind()

        for i in range(total):
            self.assertEqual((yield next(found)), obs[i])

    def test_rewind_dry(self):
        return self.assertFailure(self.d.wrapper.rewind("wefwefwef"), DatabaseException)

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
    def test_count_filter_no_collection(self):

        result = yield self.d.count({'_id': '666f6f2d6261722d71757578'})

        self.assertEqual(result, 0)

    @chainable
    def test_count_neither(self):

        result = yield self.d.count()
        self.assertEqual(result, 0)


    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
    def test_find_one_and_update_collection(self):

        obs = [{'test': 1, '_id': str(ObjectId())}]
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        yield self.d.find_one_and_update({'test': 1}, {'$set': {'test2': 0}})
        self.db._get_collection.assert_called_once_with('test_collection', False)

    @chainable
    def test_find_one_and_update_no_collection(self):

        result = yield self.d.find_one_and_update({'_id': '666f6f2d6261722d71757578'}, {'$set': {'test': 6}})

        self.assertEqual(result, None)

    @chainable
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

    @chainable
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

    @chainable
    def test_find_one_and_replace_upsert2(self):

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        found = yield self.d.find_one_and_replace({'test': 0}, {'test2': 100}, upsert=True)
        self.db._get_collection.assert_called_once_with('test_collection', True)

        found2 = yield self.d.find_one({'test': 0})
        found3 = yield self.d.find_one({'test2': 100})

        self.assertEqual(found, None)
        self.assertEqual(found2, None)
        self.assertEqual(found3['test2'], 100)

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
    def test_find_one_and_replace_collection(self):

        obs = [{'test': 1, '_id': str(ObjectId())}]
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        yield self.d.find_one_and_replace({'test': 1}, {'test2': 0})
        self.db._get_collection.assert_called_once_with('test_collection', False)

    @chainable
    def test_find_one_and_replace_no_collection(self):

        result = yield self.d.find_one_and_replace({'_id': '666f6f2d6261722d71757578'}, {'test': 6})

        self.assertEqual(result, None)

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
    def test_find_one_and_delete_collection(self):

        obs = [{'test': 1, '_id': str(ObjectId())}]
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        yield self.d.find_one_and_delete({'test': 1}, {'test2': 0})
        self.db._get_collection.assert_called_once_with('test_collection')

    @chainable
    def test_find_one_and_delete_no_collection(self):

        result = yield self.d.find_one_and_delete({'_id': '666f6f2d6261722d71757578'}, {'test': 6})

        self.assertEqual(result, None)

    @chainable
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

    @chainable
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

    @chainable
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

    @chainable
    def test_distinct_collection(self):

        obs = [{'test': 1, '_id': str(ObjectId())}]
        yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
        yield self.d.distinct('test')
        self.db._get_collection.assert_called_once_with('test_collection')

    @chainable
    def test_distinct_no_collection(self):

        result = yield self.d.distinct('test')

        self.assertEqual(result, [])

    @chainable
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
        list = yield found.to_list()
        self.assertEqual(list[0], {'_id': '0', 'count': 49})
        self.assertEqual(list[1], {'_id': '1', 'count': 149})

    @chainable
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
        list = yield found.to_list()
        for i in range(total * 2 - 51):
            self.assertEqual(list[i], {'_id': str(51 + i), 'count': 1 if i >= 49 else 2})

    @chainable
    def test_aggregate_no_collection(self):

        result = yield self.d.aggregate([])

        self.assertSequenceEqual((yield result.to_list()), [])

    @chainable
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

    @chainable
    def test_delete_one_no_collection(self):

        result = yield self.d.delete_one({})

        self.assertEqual(result, 0)

    @chainable
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

    @chainable
    def test_delete_many_no_collection(self):

        result = yield self.d.delete_many({})

        self.assertEqual(result, 0)

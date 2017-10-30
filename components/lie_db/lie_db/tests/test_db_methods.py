# coding=utf-8

import datetime

import mongomock
import pytz
import twisted
from bson import ObjectId
from copy import deepcopy
from mock import mock, call
from twisted.internet import reactor

from lie_db.db_methods import logger
from lie_db.mongo_client_wrapper import MongoClientWrapper
from mdstudio.db.model import Model
from mdstudio.db.sort_mode import SortMode
from mdstudio.deferred.chainable import chainable
from mdstudio.unittest import wait_for_completion
from mdstudio.unittest.mongo import TrialDBTestCase

twisted.internet.base.DelayedCall.debug = True

class TestMongoDatabaseWrapper(TrialDBTestCase):
    def setUp(self):
        self.db = MongoClientWrapper("localhost", 27127).get_namespace('testns')
        self.d = Model(self.db, 'test_collection')

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

        wait_for_completion.wait_for_completion = True

    def tearDown(self):
        wait_for_completion.wait_for_completion = False


    def test_transform_to_datetime(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        self.db._transform_to_datetime(document, ['date'])
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
        })

    def test_transform_to_datetime_nested(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'o': {
                'date2': '2017-9-26T09:16:00+00:00'
            }
        }
        self.db._transform_to_datetime(document, ['date', 'o.date2'])
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'o': {
                'date2': datetime.datetime(2017, 9, 26, 9, 16, tzinfo=pytz.utc)
            }
        })

    def test_transform_to_datetime_overnested(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'o': {
                'date2': '2017-9-26T09:16:00+00:00'
            }
        }
        self.db._transform_to_datetime(document, ['o.o.date2'])
        self.assertEqual(document, {
            'date': '2017-10-26T09:16:00+00:00',
            'o': {
                'date2': '2017-9-26T09:16:00+00:00'
            }
        })

    def test_transform_to_datetime_no_conversion(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'f': '2017-10-26T09:15:00+00:00'
        }
        self.db._transform_to_datetime(document, ['date'])
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'f': '2017-10-26T09:15:00+00:00'
        })

    def test_transform_to_datetime_list(self):
        document = {
            'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00']
        }
        self.db._transform_to_datetime(document, ['date'])
        self.assertEqual(document, {
            'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                     datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)]
        })

    def test_transform_to_datetime_object_list(self):
        document = {
            'dates': [
                {
                    'date': '2017-10-26T09:16:00+00:00'
                },
                {
                    'date': '2017-10-26T09:15:00+00:00'
                }
            ]
        }
        self.db._transform_to_datetime(document, ['dates.date'])
        self.assertEqual(document, {
            'dates': [
                {
                    'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
                },
                {
                    'date': datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)
                }
            ]
        })

    def test_transform_to_datetime_object_list2(self):
        document = {
            'dates': [
                {
                    'date': {
                        'o': '2017-10-26T09:16:00+00:00'
                    }
                },
                {
                    'date': {
                        'o': '2017-10-26T09:15:00+00:00'
                    }
                }
            ]
        }
        self.db._transform_to_datetime(document, ['dates.date.o'])
        self.assertEqual(document, {
            'dates': [
                {
                    'date': {
                        'o': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
                    }
                },
                {
                    'date': {
                        'o': datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)
                    }
                }
            ]
        })

    def test_transform_to_datetime_object_list_nonexisting(self):
        document = {
            'dates': [
                {
                    'date': '2017-10-26T09:16:00+00:00'
                },
                {
                    'date2': '2017-10-26T09:15:00+00:00'
                }
            ]
        }
        self.db._transform_to_datetime(document, ['dates.date'])
        self.assertEqual(document, {
            'dates': [
                {
                    'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
                },
                {
                    'date2': '2017-10-26T09:15:00+00:00'
                }
            ]
        })

    def test_transform_to_datetime_none(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'f': '2017-10-26T09:15:00+00:00'
        }
        cdocument = deepcopy(document)
        self.db._transform_to_datetime(cdocument, None)
        self.assertEqual(cdocument, document)

    def test_transform_to_datetime_nonexisting_key(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        cdocument = deepcopy(document)
        self.db._transform_to_datetime(cdocument, ['date2'])
        self.assertEqual(cdocument, document)

    def test_transform_to_datetime_prefixes_none(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        cdocument = deepcopy(document)
        self.db._transform_to_datetime(cdocument, ['date'], ['insert'])
        self.assertEqual(cdocument, document)

    def test_transform_to_datetime_prefixes(self):
        document = {
            'insert': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        }
        self.db._transform_to_datetime(document, ['date'], ['insert'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
            }
        })

    def test_transform_to_datetime_prefixes2(self):
        document = {
            'insert': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'inserts': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'insert2': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        }
        self.db._transform_to_datetime(document, ['date'], ['insert', 'inserts'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
            },
            'inserts': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
            },
            'insert2': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        })

    def test_transform_to_datetime_prefixes_existing(self):
        document = {
            'insert': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'inserts': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'insert2': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        }
        self.db._transform_to_datetime(document, ['insert.date'], ['insert', 'inserts'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
            },
            'inserts': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'insert2': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        })

    def test_transform_datetime_to_isostring(self):
        document = {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'f': '2017-10-26T09:15:00+00:00'
        }
        self.db._transform_datetime_to_isostring(document)
        self.assertEqual(document, {
            'date': '2017-10-26T09:16:00+00:00',
            'f': '2017-10-26T09:15:00+00:00'
        })


    def test_transform_datetime_to_isostring_nested(self):
        document = {
            'o': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                'f': '2017-10-26T09:15:00+00:00'
            }
        }
        self.db._transform_datetime_to_isostring(document)
        self.assertEqual(document, {
            'o': {
                'date': '2017-10-26T09:16:00+00:00',
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_transform_datetime_to_isostring_nested_list(self):
        document = {
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc), datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        }
        self.db._transform_datetime_to_isostring(document)
        self.assertEqual(document, {
            'o': {
                'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00'],
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_json(self):
        document = {
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc), datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        self.db._prepare_for_json(document)

        self.assertEqual(document, {
            'o': {
                'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00'],
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_json_id(self):
        document = {
            '_id': 1000,
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc), datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        self.db._prepare_for_json(document)

        self.assertEqual(document, {
            '_id': '1000',
            'o': {
                'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00'],
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_json_none(self):
        document = None

        self.db._prepare_for_json(document)

        self.assertEqual(document, None)

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

        with mock.patch('lie_db.db_methods.logger.info'):

            collection = {
                'name': 'test_collection'
            }
            self.assertEqual(self.db._get_collection(collection), None)
            logger.info.assert_not_called()

    def test_get_collection_dict_create(self):

        with mock.patch('lie_db.db_methods.logger.info'):
            collection = {
                'name': 'test_collection'
            }
            self.assertIsInstance(self.db._get_collection(collection,create=True), mongomock.collection.Collection)

            logger.info.assert_called_once_with('Creating collection {collection} in {namespace}', collection='test_collection', namespace='testns')

    def test_get_collection_str(self):

        with mock.patch('lie_db.db_methods.logger.info'):

            collection = 'test_collection'
            self.assertEqual(self.db._get_collection(collection), None)
            logger.info.assert_not_called()

    def test_get_collection_str_create(self):

        with mock.patch('lie_db.db_methods.logger.info'):
            collection = 'test_collection'
            self.assertIsInstance(self.db._get_collection(collection,create=True), mongomock.collection.Collection)

            logger.info.assert_called_once_with('Creating collection {collection} in {namespace}', collection='test_collection', namespace='testns')

    def test_get_collection_exists(self):

        with mock.patch('lie_db.db_methods.logger.info'):
            collection = 'test_collection'
            col = self.db._get_collection(collection,create=True)
            self.assertIsInstance(col, mongomock.collection.Collection)

            logger.info.assert_called_once_with('Creating collection {collection} in {namespace}', collection='test_collection', namespace='testns')

            self.assertIs(self.db._get_collection(collection), col)

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
    def test_insert_one_date_fields(self):
        self.db._transform_to_datetime = mock.MagicMock()

        id = yield self.d.insert_one({'test': 2}, date_fields=['date'])

        self.db._transform_to_datetime.assert_called_once_with({'insert': {'test': 2, '_id': ObjectId(id)}}, ['date'], ['insert'])

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
        ], ['date'])

        self.db._get_collection.assert_called_once_with('test_collection', True)

    @chainable
    def test_insert_many_date_fields(self):

        self.db._transform_to_datetime = mock.MagicMock()
        ids = yield self.d.insert_many([
            {'test': 2},
            {'test': 3}
        ], ['date'])

        self.db._transform_to_datetime.assert_called_once_with({
            'insert': [
                {'test': 2, '_id': ObjectId(ids[0])},
                {'test': 3, '_id': ObjectId(ids[1])}
            ]}, ['date'], ['insert'])

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
        self.db._prepare_for_mongo.assert_has_calls([call(obs),call({'_id': '59f1d9c57dd5d70043e74f8d'}),call({'test2': 6})])

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
    def test_replace_one_datefields(self):

        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ])
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        self.db._transform_to_datetime = mock.MagicMock()
        yield self.d.replace_one({'_id': '666f6f2d6261722d71757578'}, {'test': 6})

        self.db._transform_to_datetime.assert_called_once_with({
            'filter': {
                '_id': ObjectId('666f6f2d6261722d71757578')
            },
            'replacement': {
                'test': 6
            }
        }, None, ['filter', 'replacement'])

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
        self.db._prepare_for_mongo.assert_has_calls([call(obs),call({'_id': '59f1d9c57dd5d70043e74f8d'}),call({'$set': {'test': 6}})])

        found1 = yield self.d.find_one({'_id': ids[0]})
        self.assertEqual(found1, {'test': 2, '_id': ids[0]})
        found2 = yield self.d.find_one({'_id': ids[1]})
        self.assertEqual(found2, {'test': 6, '_id': ids[1]})

        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

    @chainable
    def test_update_one_functionality(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = [
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 2, '_id': '59f1d9c57dd5d70043e74f8d'},
            {'test': 6, '_id': '666f6f2d6261722d71757578'}
        ]
        ids = yield self.d.insert_many(obs)

        self.db._get_collection = mock.MagicMock(wraps=self.db._get_collection)
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
    def test_update_one_datefields(self):

        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ])
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        self.db._transform_to_datetime = mock.MagicMock()
        yield self.d.update_one({'_id': '666f6f2d6261722d71757578'}, {'$set':{'test': 6}})

        self.db._transform_to_datetime.assert_called_once_with({
            'filter': {
                '_id': ObjectId('666f6f2d6261722d71757578')
            },
            'update': {
                '$set': {'test': 6}
            }
        }, None, ['filter', 'update'])

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
        self.db._prepare_for_mongo.assert_has_calls([call(obs),call({'_id': '59f1d9c57dd5d70043e74f8d'}),call({'$set': {'test': 6}})])

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
    def test_update_many_datefields(self):

        ids = yield self.d.insert_many([
            {'test': 2, '_id': '0123456789ab0123456789ab'},
            {'test': 3, '_id': '59f1d9c57dd5d70043e74f8d'},
        ])
        self.assertEqual(ids, ['0123456789ab0123456789ab', '59f1d9c57dd5d70043e74f8d'])

        self.db._transform_to_datetime = mock.MagicMock()
        yield self.d.update_many({'_id': '666f6f2d6261722d71757578'}, {'$set':{'test': 6}})

        self.db._transform_to_datetime.assert_called_once_with({
            'filter': {
                '_id': ObjectId('666f6f2d6261722d71757578')
            },
            'update': {
                '$set': {'test': 6}
            }
        }, None, ['filter', 'update'])

    @chainable
    def test_find_one(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(500):
            obs.append({'test': i, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        for i in range(500):
            found = yield self.d.find_one({'test': i})
            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])

    @chainable
    def test_find_one_projection(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(500):
            obs.append({'test': i, '_id': str(ObjectId())})
        yield self.d.insert_many(obs)

        for i in range(500):
            found = yield self.d.find_one({'test': i}, {'_id': 0})
            self.assertEqual(found, {'test': i})

    @chainable
    def test_find_one_skip(self):

        self.db._prepare_for_mongo = mock.MagicMock(wraps=self.db._prepare_for_mongo)
        obs = []
        for i in range(500):
            obs.append({'test': i, 'test2': 0, '_id': str(ObjectId())})
        for i in range(500):
            obs.append({'test': i, 'test2': 1, '_id': str(ObjectId())})
        ids = yield self.d.insert_many(obs)

        all = yield self.d.find_many({})

        for i in range(500):
            found = yield self.d.find_one({'test': i}, sort=('_id', SortMode.Desc))
            self.assertEqual(obs[i+500]['_id'], ids[i+500])
            self.assertEqual(found, obs[i+500])

        for i in range(500):
            found = yield self.d.find_one({'test': i}, sort=('_id', SortMode.Asc))
            self.assertEqual(obs[i]['_id'], ids[i])
            self.assertEqual(found, obs[i])
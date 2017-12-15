# coding=utf-8

import mock
import pytz
from autobahn.twisted import ApplicationSession
from faker import Faker
from twisted.trial.unittest import TestCase

from mdstudio.db.cursor import Cursor
from mdstudio.db.database import IDatabase
from mdstudio.db.fields import Fields
from mdstudio.service.model import Model
from mdstudio.db.response import ReplaceOneResponse, UpdateOneResponse, UpdateManyResponse
from mdstudio.db.session_database import SessionDatabaseWrapper
from mdstudio.db.sort_mode import SortMode
from mdstudio.deferred.chainable import chainable


# noinspection PyCallByClass,PyTypeChecker
class ModelTests(TestCase):
    faker = Faker()

    def setUp(self):
        self.wrapper = mock.MagicMock(spec=SessionDatabaseWrapper)
        self.wrapper._check_wrapper = mock.MagicMock()
        self.collection = 'coll'
        self.model = Model(self.wrapper, self.collection)
        self.time = self.faker.date_time(pytz.utc)
        self.time2 = self.faker.date_time(pytz.utc)
        self.document = {
            '_id': 'test_id',
            'test': 1234,
            'updatedAt': self.time.isoformat(),
            'foo': {
                'bar': False
            }
        }
        self.document2 = {
            '_id': 'test_id',
            'test': 1235,
            'updatedAt': self.time2.isoformat(),
            'foo': {
                'bar': True
            }
        }
        self.documents = [self.document, self.document2]

    def test_construction(self):
        self.wrapper = mock.Mock(spec=IDatabase)
        self.collection = 'coll'
        self.model = Model(self.wrapper, self.collection)
        self.assertEqual(self.model.wrapper, self.wrapper)

    def test_construction2(self):
        self.assertEqual(self.model.wrapper, self.wrapper)

        self.assertIsInstance(self.model.wrapper, SessionDatabaseWrapper)

    def test_construction3(self):
        self.wrapper = mock.MagicMock(spec=SessionDatabaseWrapper)

        self.model = Model(self.wrapper, self.collection)
        self.assertEqual(self.model.wrapper, self.wrapper)

        self.assertIsInstance(self.model.wrapper, SessionDatabaseWrapper)

    def test_construction4(self):
        self.wrapper = mock.MagicMock(spec=ApplicationSession)

        self.assertRaises(AssertionError, Model, self.wrapper, self.collection)

    def test_construction_class(self):
        class Users(Model):
            pass

        self.model = Users(self.wrapper)

        self.assertEqual(self.model.collection, 'users')

    def test_construction_class_override(self):
        class Users(Model):
            pass

        self.model = Users(self.wrapper, self.collection)

        self.assertEqual(self.model.collection, self.collection)

    def test_insert_one(self):
        self.wrapper.insert_one.return_value = {'id': '12345'}
        self.wrapper.extract = IDatabase.extract
        result = self.model.insert_one(self.document)

        self.assertEqual(result, '12345')

        self.wrapper.insert_one.assert_called_once_with(self.collection,
                                                        insert=self.document,
                                                        fields=None)

    def test_insert_one_date_time_fields(self):
        self.wrapper.insert_one.return_value = {'id': '12345'}
        self.wrapper.extract = IDatabase.extract
        result = self.model.insert_one(self.document, fields=Fields(date_times=['test']))

        self.assertEqual(result, '12345')

        self.wrapper.insert_one.assert_called_once_with(self.collection,
                                                        insert=self.document,
                                                        fields=Fields(date_times=['test']))

    def test_insert_one_date_time_fields_inject(self):
        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_one.return_value = {'id': '12345'}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper)
        result = self.model.insert_one(self.document, fields=Fields(date_times=['test']))

        self.assertEqual(result, '12345')

        self.wrapper.insert_one.assert_called_once_with('users',
                                                        insert=self.document,
                                                        fields=Fields(date_times=['test', 'datefields']))

    def test_insert_one_date_time_fields_only_inject(self):
        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_one.return_value = {'id': '12345'}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper)
        result = self.model.insert_one(self.document)

        self.assertEqual(result, '12345')

        self.wrapper.insert_one.assert_called_once_with('users',
                                                        insert=self.document,
                                                        fields=Fields(date_times=['datefields']))

    def test_insert_many(self):
        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        result = self.model.insert_many(self.documents)

        self.assertEqual(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with(self.collection,
                                                         insert=self.documents,
                                                         fields=None)

    def test_insert_many_date_time_fields(self):
        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        result = self.model.insert_many(self.documents, fields=Fields(date_times=['test']))

        self.assertEqual(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with(self.collection,
                                                         insert=self.documents,
                                                         fields=Fields(date_times=['test']))

    def test_insert_many_date_time_fields_inject(self):
        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper)
        result = self.model.insert_many(self.documents, fields=Fields(date_times=['test']))

        self.assertEqual(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with('users',
                                                         insert=self.documents,
                                                         fields=Fields(date_times=['test', 'datefields']))

    def test_insert_many_date_time_fields_only_inject(self):
        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper)
        result = self.model.insert_many(self.documents)

        self.assertEqual(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with('users',
                                                         insert=self.documents,
                                                         fields=Fields(date_times=['datefields']))

    @chainable
    def test_replace_one(self):
        self.wrapper.replace_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        result = yield self.model.replace_one({'_id': 'test_id'}, self.document)

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

        self.wrapper.replace_one.assert_called_once_with(self.collection,
                                                         filter={'_id': 'test_id'},
                                                         replacement=self.document,
                                                         upsert=False,
                                                         fields=None)

    @chainable
    def test_replace_one_upsert(self):
        self.wrapper.replace_one.return_value = {
            'matched': 0,
            'modified': 1,
            'upsertedId': 'test_id2'
        }
        self.wrapper.transform = IDatabase.transform
        result = yield self.model.replace_one({'_id': 'test_id'}, self.document, upsert=True)

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, 'test_id2')

        self.wrapper.replace_one.assert_called_once_with(self.collection,
                                                         filter={'_id': 'test_id'},
                                                         replacement=self.document,
                                                         upsert=True,
                                                         fields=None)

    @chainable
    def test_replace_one_date_time_fields(self):
        self.wrapper.replace_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        result = yield self.model.replace_one({'_id': 'test_id'}, self.document, fields=Fields(date_times=['test']))

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

        self.wrapper.replace_one.assert_called_once_with(self.collection,
                                                         filter={'_id': 'test_id'},
                                                         replacement=self.document,
                                                         upsert=False,
                                                         fields=Fields(date_times=['test']))

    @chainable
    def test_replace_one_date_time_fields_inject(self):
        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.replace_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        self.model = Users(self.wrapper)
        result = yield self.model.replace_one({'_id': 'test_id'}, self.document, fields=Fields(date_times=['test']))

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

        self.wrapper.replace_one.assert_called_once_with('users',
                                                         filter={'_id': 'test_id'},
                                                         replacement=self.document,
                                                         upsert=False,
                                                         fields=Fields(date_times=['test', 'datefields']))

    @chainable
    def test_replace_one_date_time_fields_only_inject(self):
        class Users(Model):
            date_time_fields = ['date_time_fields']

        self.wrapper.replace_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        self.model = Users(self.wrapper)
        result = yield self.model.replace_one({'_id': 'test_id'}, self.document)

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

        self.wrapper.replace_one.assert_called_once_with('users',
                                                         filter={'_id': 'test_id'},
                                                         replacement=self.document,
                                                         upsert=False,
                                                         fields=Fields(date_times=['date_time_fields']))

    def test_count(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count()

        self.assertEqual(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection,
                                                   filter=None,
                                                   skip=None,
                                                   limit=None,
                                                   fields=None,
                                                   cursor_id=None,
                                                   with_limit_and_skip=False)

    def test_count_filter(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count({'_id': 'test_id'})

        self.assertEqual(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection,
                                                   filter={'_id': 'test_id'},
                                                   skip=None,
                                                   limit=None,
                                                   fields=None,
                                                   cursor_id=None,
                                                   with_limit_and_skip=False)

    def test_count_skip(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count(skip=10)

        self.assertEqual(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection,
                                                   filter=None,
                                                   skip=10,
                                                   limit=None,
                                                   fields=None,
                                                   cursor_id=None,
                                                   with_limit_and_skip=False)

    def test_count_limit(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count(limit=10)

        self.assertEqual(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection,
                                                   filter=None,
                                                   skip=None,
                                                   limit=10,
                                                   fields=None,
                                                   cursor_id=None,
                                                   with_limit_and_skip=False)

    def test_count_date_field(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        self.model.date_time_fields = ['test2']
        result = self.model.count(cursor_id='test_id', fields=Fields(date_times=['test']))

        self.assertEqual(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection,
                                                   filter=None,
                                                   skip=None,
                                                   limit=None,
                                                   fields=Fields(date_times=['test', 'test2']),
                                                   cursor_id='test_id',
                                                   with_limit_and_skip=False)

    def test_count_cursor_id(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count(cursor_id='test_id')

        self.assertEqual(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection,
                                                   filter=None,
                                                   skip=None,
                                                   limit=None,
                                                   fields=None,
                                                   cursor_id='test_id',
                                                   with_limit_and_skip=False)

    def test_count_cursor_id_with_limit_and_skip(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count(cursor_id='test_id', with_limit_and_skip=True)

        self.assertEqual(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection,
                                                   filter=None,
                                                   skip=None,
                                                   limit=None,
                                                   fields=None,
                                                   cursor_id='test_id',
                                                   with_limit_and_skip=True)

    @chainable
    def test_update_one(self):
        self.wrapper.update_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        result = yield self.model.update_one({'_id': 'test_id'}, self.document)

        self.assertIsInstance(result, UpdateOneResponse)
        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

        self.wrapper.update_one.assert_called_once_with(self.collection,
                                                        filter={'_id': 'test_id'},
                                                        update=self.document,
                                                        upsert=False,
                                                        fields=None)

    @chainable
    def test_update_one_upsert(self):
        self.wrapper.update_one.return_value = {
            'matched': 0,
            'modified': 1,
            'upsertedId': '1234'
        }
        self.wrapper.transform = IDatabase.transform
        result = yield self.model.update_one({'_id': 'test_id'}, self.document, True)

        self.assertIsInstance(result, UpdateOneResponse)
        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, '1234')

        self.wrapper.update_one.assert_called_once_with(self.collection,
                                                        filter={'_id': 'test_id'},
                                                        update=self.document,
                                                        upsert=True,
                                                        fields=None)

    @chainable
    def test_update_one_date_time_fields(self):
        self.wrapper.update_one.return_value = {
            'matched': 0,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        self.model.date_time_fields = ['test2']
        result = yield self.model.update_one({'_id': 'test_id'}, self.document, fields=Fields(date_times=['test']))

        self.assertIsInstance(result, UpdateOneResponse)
        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

        self.wrapper.update_one.assert_called_once_with(self.collection,
                                                        filter={'_id': 'test_id'},
                                                        update=self.document,
                                                        upsert=False,
                                                        fields=Fields(date_times=['test', 'test2']))

    @chainable
    def test_update_many(self):
        self.wrapper.update_many.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        result = yield self.model.update_many({'_id': 'test_id'}, self.document)

        self.assertIsInstance(result, UpdateManyResponse)
        self.assertEqual(result.matched, 1)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

        self.wrapper.update_many.assert_called_once_with(self.collection,
                                                         filter={'_id': 'test_id'},
                                                         update=self.document,
                                                         upsert=False,
                                                         fields=None)

    @chainable
    def test_update_many_upsert(self):
        self.wrapper.update_many.return_value = {
            'matched': 0,
            'modified': 1,
            'upsertedId': '1234'
        }
        self.wrapper.transform = IDatabase.transform
        result = yield self.model.update_many({'_id': 'test_id'}, self.document, True)

        self.assertIsInstance(result, UpdateManyResponse)
        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, '1234')

        self.wrapper.update_many.assert_called_once_with(self.collection,
                                                         filter={'_id': 'test_id'},
                                                         update=self.document,
                                                         upsert=True,
                                                         fields=None)

    @chainable
    def test_update_many_date_time_fields(self):
        self.wrapper.update_many.return_value = {
            'matched': 0,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        self.model.date_time_fields = ['test2']
        result = yield self.model.update_many({'_id': 'test_id'}, self.document, fields=Fields(date_times=['test']))

        self.assertIsInstance(result, UpdateManyResponse)
        self.assertEqual(result.matched, 0)
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.upserted_id, None)

        self.wrapper.update_many.assert_called_once_with(self.collection,
                                                         filter={'_id': 'test_id'},
                                                         update=self.document,
                                                         upsert=False,
                                                         fields=Fields(date_times=['test', 'test2']))

    @chainable
    def test_find_one(self):
        self.wrapper.find_one.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one({'_id': 'test_id'})

        self.assertEqual(result, self.document)

        self.wrapper.find_one.assert_called_once_with(self.collection,
                                                      filter={'_id': 'test_id'},
                                                      projection=None,
                                                      skip=None,
                                                      sort=None,
                                                      fields=None)

    @chainable
    def test_find_one_projection(self):
        self.wrapper.find_one.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one({'_id': 'test_id'}, {'_id': 'id'})

        self.assertEqual(result, self.document)

        self.wrapper.find_one.assert_called_once_with(self.collection,
                                                      filter={'_id': 'test_id'},
                                                      projection={'_id': 'id'},
                                                      skip=None,
                                                      sort=None,
                                                      fields=None)

    @chainable
    def test_find_one_skip(self):
        self.wrapper.find_one.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one({'_id': 'test_id'}, skip=10)

        self.assertEqual(result, self.document)

        self.wrapper.find_one.assert_called_once_with(self.collection,
                                                      filter={'_id': 'test_id'},
                                                      projection=None,
                                                      skip=10,
                                                      sort=None,
                                                      fields=None)

    @chainable
    def test_find_one_sort(self):
        self.wrapper.find_one.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one({'_id': 'test_id'}, sort=[('_id', SortMode.Desc)])

        self.assertEqual(result, self.document)

        self.wrapper.find_one.assert_called_once_with(self.collection,
                                                      filter={'_id': 'test_id'},
                                                      projection=None,
                                                      skip=None,
                                                      sort=[('_id', SortMode.Desc)],
                                                      fields=None)

    @chainable
    def test_find_one_date_field(self):
        self.wrapper.find_one.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        self.model.date_time_fields = ['updatedAt']
        result = yield self.model.find_one({'_id': 'test_id'}, fields=Fields(date_times=['updatedAt']))

        self.assertEqual(result, self.document)

        self.wrapper.find_one.assert_called_once_with(self.collection,
                                                      filter={'_id': 'test_id'},
                                                      projection=None,
                                                      skip=None,
                                                      sort=None,
                                                      fields=Fields(date_times=['updatedAt', 'updatedAt']))

    @chainable
    def test_find_one_model_date_field(self):
        class TestModel(Model):
            date_time_fields = ['createdAt']

        self.model = TestModel(self.wrapper, self.collection)
        self.model.fields = mock.MagicMock(wraps=self.model.fields)
        time = self.faker.date_time(tzinfo=pytz.utc)
        self.wrapper.find_one.return_value = {
            'result': {
                'createdAt': time.isoformat(),
                'value': 123456
            }
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one({'_id': 'test_id'})

        self.assertEqual(result, {
            'value': 123456,
            'createdAt': time
        })

        self.wrapper.find_one.assert_called_once_with(self.collection,
                                                      filter={'_id': 'test_id'},
                                                      projection=None,
                                                      skip=None,
                                                      sort=None,
                                                      fields=Fields(date_times=['createdAt']))

        self.model.fields.assert_called_once_with(None)

    # noinspection PyCallByClass
    @chainable
    def test_find_many(self):
        self.wrapper.find_many.return_value = {
            'cursorId': 1234,
            'alive': False,
            'results': self.documents
        }
        self.wrapper.make_cursor = lambda x, fields: IDatabase.make_cursor(self.wrapper, x, fields)
        results = yield self.model.find_many({'_id': 'test_id'})

        self.assertIsInstance(results, Cursor)

        lresults = yield results.to_list()
        self.assertEqual(lresults[0], self.document)
        self.assertEqual(lresults[1], self.document2)

        self.wrapper.find_many.assert_called_once_with(self.collection,
                                                       filter={'_id': 'test_id'},
                                                       projection=None,
                                                       skip=None,
                                                       limit=None,
                                                       sort=None,
                                                       fields=None)

    @chainable
    def test_find_many_projection(self):
        self.wrapper.find_many.return_value = {
            'cursorId': 1234,
            'alive': False,
            'results': self.documents
        }
        self.wrapper.make_cursor = lambda x, fields: IDatabase.make_cursor(self.wrapper, x, fields)
        results = yield self.model.find_many({'_id': 'test_id'}, projection={'_id': 'id'})

        self.assertIsInstance(results, Cursor)

        lresults = yield results.to_list()
        self.assertEqual(lresults[0], self.document)
        self.assertEqual(lresults[1], self.document2)

        self.wrapper.find_many.assert_called_once_with(self.collection,
                                                       filter={'_id': 'test_id'},
                                                       projection={'_id': 'id'},
                                                       skip=None,
                                                       limit=None,
                                                       sort=None,
                                                       fields=None)

    @chainable
    def test_find_many_skip(self):
        self.wrapper.find_many.return_value = {
            'cursorId': 1234,
            'alive': False,
            'results': self.documents
        }
        self.wrapper.make_cursor = lambda x, fields: IDatabase.make_cursor(self.wrapper, x, fields)
        results = yield self.model.find_many({'_id': 'test_id'}, skip=10)

        self.assertIsInstance(results, Cursor)

        lresults = yield results.to_list()
        self.assertEqual(lresults[0], self.document)
        self.assertEqual(lresults[1], self.document2)

        self.wrapper.find_many.assert_called_once_with(self.collection,
                                                       filter={'_id': 'test_id'},
                                                       projection=None,
                                                       skip=10,
                                                       limit=None,
                                                       sort=None,
                                                       fields=None)

    @chainable
    def test_find_many_limit(self):
        self.wrapper.find_many.return_value = {
            'cursorId': 1234,
            'alive': False,
            'results': self.documents
        }
        self.wrapper.make_cursor = lambda x, fields: IDatabase.make_cursor(self.wrapper, x, fields)
        results = yield self.model.find_many({'_id': 'test_id'}, limit=10)

        self.assertIsInstance(results, Cursor)

        lresults = yield results.to_list()
        self.assertEqual(lresults[0], self.document)
        self.assertEqual(lresults[1], self.document2)

        self.wrapper.find_many.assert_called_once_with(self.collection,
                                                       filter={'_id': 'test_id'},
                                                       projection=None,
                                                       skip=None,
                                                       limit=10,
                                                       sort=None,
                                                       fields=None)

    @chainable
    def test_find_many_sort(self):
        self.wrapper.find_many.return_value = {
            'cursorId': 1234,
            'alive': False,
            'results': self.documents
        }
        self.wrapper.make_cursor = lambda x, fields: IDatabase.make_cursor(self.wrapper, x, fields)
        results = yield self.model.find_many({'_id': 'test_id'}, sort=[('_id', SortMode.Desc)])

        self.assertIsInstance(results, Cursor)

        lresults = yield results.to_list()
        self.assertEqual(lresults[0], self.document)
        self.assertEqual(lresults[1], self.document2)

        self.wrapper.find_many.assert_called_once_with(self.collection,
                                                       filter={'_id': 'test_id'},
                                                       projection=None,
                                                       skip=None,
                                                       limit=None,
                                                       sort=[('_id', SortMode.Desc)],
                                                       fields=None)

    @chainable
    def test_find_many_date_time_fields(self):
        self.wrapper.find_many.return_value = {
            'cursorId': 1234,
            'alive': False,
            'results': self.documents
        }
        self.wrapper.make_cursor = lambda x, fields: IDatabase.make_cursor(self.wrapper, x, fields)
        self.model.date_time_fields = ['updatedAt']
        results = yield self.model.find_many({'_id': 'test_id'}, fields=Fields(date_times=['updatedAt']))

        self.assertIsInstance(results, Cursor)

        lresults = yield results.to_list()
        self.assertEqual(lresults[0], self.document)
        self.assertEqual(lresults[1], self.document2)

        self.wrapper.find_many.assert_called_once_with(self.collection,
                                                       filter={'_id': 'test_id'},
                                                       projection=None,
                                                       skip=None,
                                                       limit=None,
                                                       sort=None,
                                                       fields=Fields(date_times=['updatedAt', 'updatedAt']))

    @chainable
    def test_find_many_model_date_time_fields(self):
        class TestModel(Model):
            date_time_fields = ['updatedAt']

        self.wrapper.find_many.return_value = {
            'cursorId': 1234,
            'alive': False,
            'results': self.documents
        }
        self.model = TestModel(self.wrapper, self.collection)
        self.wrapper.make_cursor = lambda x, fields: IDatabase.make_cursor(self.wrapper, x, fields)
        results = yield self.model.find_many({'_id': 'test_id'})

        self.assertIsInstance(results, Cursor)

        lresults = yield results.to_list()
        self.assertEqual(lresults[0], {
            '_id': 'test_id',
            'foo': {'bar': False},
            'test': 1234,
            'updatedAt': self.time
        })
        self.assertEqual(lresults[1], {
            '_id': 'test_id',
            'foo': {'bar': True},
            'test': 1235,
            'updatedAt': self.time2
        })

        self.wrapper.find_many.assert_called_once_with(self.collection,
                                                       filter={'_id': 'test_id'},
                                                       projection=None,
                                                       skip=None,
                                                       limit=None,
                                                       sort=None,
                                                       fields=Fields(date_times=['updatedAt']))

    @chainable
    def test_find_many_model_date_time_fields_2(self):
        class TestModel(Model):
            date_time_fields = ['updatedAt']

        self.wrapper.find_many.return_value = {
            'cursorId': 1234,
            'alive': True,
            'results': self.documents
        }
        self.model = TestModel(self.wrapper, self.collection)
        self.wrapper.make_cursor = lambda x, fields: IDatabase.make_cursor(self.wrapper, x, fields)
        results = yield self.model.find_many({'_id': 'test_id'})

        self.assertIsInstance(results, Cursor)

        lresults = yield results.to_list()
        self.assertEqual(lresults[0], {
            '_id': 'test_id',
            'foo': {'bar': False},
            'test': 1234,
            'updatedAt': self.time
        })
        self.assertEqual(lresults[1], {
            '_id': 'test_id',
            'foo': {'bar': True},
            'test': 1235,
            'updatedAt': self.time2
        })

        self.wrapper.find_many.assert_called_once_with(self.collection,
                                                       filter={'_id': 'test_id'},
                                                       projection=None,
                                                       skip=None,
                                                       limit=None,
                                                       sort=None,
                                                       fields=Fields(date_times=['updatedAt']))

    @chainable
    def test_find_one_and_update(self):
        self.wrapper.find_one_and_update.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_update({'_id': 'test_id'}, self.document2)

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_update.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 update=self.document2,
                                                                 upsert=False,
                                                                 projection=None,
                                                                 sort=None,
                                                                 return_updated=False,
                                                                 fields=None)

    @chainable
    def test_find_one_and_update_projection(self):
        self.wrapper.find_one_and_update.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_update({'_id': 'test_id'}, self.document2, projection={'_id': 'id'})

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_update.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 update=self.document2,
                                                                 upsert=False,
                                                                 projection={'_id': 'id'},
                                                                 sort=None,
                                                                 return_updated=False,
                                                                 fields=None)

    @chainable
    def test_find_one_and_update_upsert(self):
        self.wrapper.find_one_and_update.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_update({'_id': 'test_id'}, self.document2, upsert=True)

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_update.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 update=self.document2,
                                                                 upsert=True,
                                                                 projection=None,
                                                                 sort=None,
                                                                 return_updated=False,
                                                                 fields=None)

    @chainable
    def test_find_one_and_update_sort(self):
        self.wrapper.find_one_and_update.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_update({'_id': 'test_id'}, self.document2, sort=[('_id', SortMode.Desc)])

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_update.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 update=self.document2,
                                                                 upsert=False,
                                                                 projection=None,
                                                                 sort=[('_id', SortMode.Desc)],
                                                                 return_updated=False,
                                                                 fields=None)

    @chainable
    def test_find_one_and_update_return_updated(self):
        self.wrapper.find_one_and_update.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_update({'_id': 'test_id'}, self.document2, return_updated=True)

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_update.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 update=self.document2,
                                                                 upsert=False,
                                                                 projection=None,
                                                                 sort=None,
                                                                 return_updated=True,
                                                                 fields=None)

    @chainable
    def test_find_one_and_update_date_field(self):
        self.wrapper.find_one_and_update.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        self.model.date_time_fields = ['updatedAt']
        result = yield self.model.find_one_and_update({'_id': 'test_id'}, self.document2, fields=Fields(date_times=['updatedAt']))

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_update.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 update=self.document2,
                                                                 upsert=False,
                                                                 projection=None,
                                                                 sort=None,
                                                                 return_updated=False,
                                                                 fields=Fields(date_times=['updatedAt', 'updatedAt']))

    @chainable
    def test_find_one_and_update_model_date_field(self):
        class TestModel(Model):
            date_time_fields = ['createdAt']

        self.model = TestModel(self.wrapper, self.collection)
        self.model.fields = mock.MagicMock(wraps=self.model.fields)
        time = self.faker.date_time(tzinfo=pytz.utc)
        self.wrapper.find_one_and_update.return_value = {
            'result': {
                'createdAt': time.isoformat(),
                'value': 123456
            }
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_update({'_id': 'test_id'}, self.document2)

        self.assertEqual(result, {
            'value': 123456,
            'createdAt': time
        })

        self.wrapper.find_one_and_update.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 update=self.document2,
                                                                 upsert=False,
                                                                 projection=None,
                                                                 sort=None,
                                                                 return_updated=False,
                                                                 fields=Fields(date_times=['createdAt']))

        self.model.fields.assert_called_once_with(None)

    @chainable
    def test_find_one_and_replace(self):
        self.wrapper.find_one_and_replace.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_replace({'_id': 'test_id'}, self.document2)

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_replace.assert_called_once_with(self.collection,
                                                                  filter={'_id': 'test_id'},
                                                                  replacement=self.document2,
                                                                  upsert=False,
                                                                  projection=None,
                                                                  sort=None,
                                                                  return_updated=False,
                                                                  fields=None)

    @chainable
    def test_find_one_and_replace_projection(self):
        self.wrapper.find_one_and_replace.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_replace({'_id': 'test_id'}, self.document2, projection={'_id': 'id'})

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_replace.assert_called_once_with(self.collection,
                                                                  filter={'_id': 'test_id'},
                                                                  replacement=self.document2,
                                                                  upsert=False,
                                                                  projection={'_id': 'id'},
                                                                  sort=None,
                                                                  return_updated=False,
                                                                  fields=None)

    @chainable
    def test_find_one_and_replace_upsert(self):
        self.wrapper.find_one_and_replace.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_replace({'_id': 'test_id'}, self.document2, upsert=True)

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_replace.assert_called_once_with(self.collection,
                                                                  filter={'_id': 'test_id'},
                                                                  replacement=self.document2,
                                                                  upsert=True,
                                                                  projection=None,
                                                                  sort=None,
                                                                  return_updated=False,
                                                                  fields=None)

    @chainable
    def test_find_one_and_replace_sort(self):
        self.wrapper.find_one_and_replace.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_replace({'_id': 'test_id'}, self.document2, sort=[('_id', SortMode.Desc)])

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_replace.assert_called_once_with(self.collection,
                                                                  filter={'_id': 'test_id'},
                                                                  replacement=self.document2,
                                                                  upsert=False,
                                                                  projection=None,
                                                                  sort=[('_id', SortMode.Desc)],
                                                                  return_updated=False,
                                                                  fields=None)

    @chainable
    def test_find_one_and_replace_return_updated(self):
        self.wrapper.find_one_and_replace.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_replace({'_id': 'test_id'}, self.document2, return_updated=True)

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_replace.assert_called_once_with(self.collection,
                                                                  filter={'_id': 'test_id'},
                                                                  replacement=self.document2,
                                                                  upsert=False,
                                                                  projection=None,
                                                                  sort=None,
                                                                  return_updated=True,
                                                                  fields=None)

    @chainable
    def test_find_one_and_replace_date_field(self):
        self.wrapper.find_one_and_replace.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        self.model.date_time_fields = ['updatedAt']
        result = yield self.model.find_one_and_replace({'_id': 'test_id'}, self.document2, fields=Fields(date_times=['updatedAt']))

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_replace.assert_called_once_with(self.collection,
                                                                  filter={'_id': 'test_id'},
                                                                  replacement=self.document2,
                                                                  upsert=False,
                                                                  projection=None,
                                                                  sort=None,
                                                                  return_updated=False,
                                                                  fields=Fields(date_times=['updatedAt', 'updatedAt']))

    @chainable
    def test_find_one_model_and_replace_date_field(self):
        class TestModel(Model):
            date_time_fields = ['createdAt']

        self.model = TestModel(self.wrapper, self.collection)
        self.model.fields = mock.MagicMock(wraps=self.model.fields)
        time = self.faker.date_time(tzinfo=pytz.utc)
        self.wrapper.find_one_and_replace.return_value = {
            'result': {
                'createdAt': time.isoformat(),
                'value': 123456
            }
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_replace({'_id': 'test_id'}, self.document2)

        self.assertEqual(result, {
            'value': 123456,
            'createdAt': time
        })

        self.wrapper.find_one_and_replace.assert_called_once_with(self.collection,
                                                                  filter={'_id': 'test_id'},
                                                                  replacement=self.document2,
                                                                  upsert=False,
                                                                  projection=None,
                                                                  sort=None,
                                                                  return_updated=False,
                                                                  fields=Fields(date_times=['createdAt']))

        self.model.fields.assert_called_once_with(None)

    @chainable
    def test_find_one_and_delete(self):
        self.wrapper.find_one_and_delete.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_delete({'_id': 'test_id'}, self.document2)

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_delete.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 projection=self.document2,
                                                                 sort=None,
                                                                 fields=None)

    @chainable
    def test_find_one_and_delete_projection(self):
        self.wrapper.find_one_and_delete.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_delete({'_id': 'test_id'}, projection={'_id': 'id'})

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_delete.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 projection={'_id': 'id'},
                                                                 sort=None,
                                                                 fields=None)

    @chainable
    def test_find_one_and_delete_sort(self):
        self.wrapper.find_one_and_delete.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_delete({'_id': 'test_id'}, sort=[('_id', SortMode.Desc)])

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_delete.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 projection=None,
                                                                 sort=[('_id', SortMode.Desc)],
                                                                 fields=None)

    @chainable
    def test_find_one_and_delete_date_field(self):
        self.wrapper.find_one_and_delete.return_value = {
            'result': self.document
        }
        self.wrapper.extract = IDatabase.extract
        self.model.date_time_fields = ['updatedAt']
        result = yield self.model.find_one_and_delete({'_id': 'test_id'}, fields=Fields(date_times=['updatedAt']))

        self.assertEqual(result, self.document)

        self.wrapper.find_one_and_delete.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 projection=None,
                                                                 sort=None,
                                                                 fields=Fields(date_times=['updatedAt', 'updatedAt']))

    @chainable
    def test_find_one_and_delete_model_date_field(self):
        class TestModel(Model):
            date_time_fields = ['createdAt']

        self.model = TestModel(self.wrapper, self.collection)
        self.model.fields = mock.MagicMock(wraps=self.model.fields)
        time = self.faker.date_time(tzinfo=pytz.utc)
        self.wrapper.find_one_and_delete.return_value = {
            'result': {
                'createdAt': time.isoformat(),
                'value': 123456
            }
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.find_one_and_delete({'_id': 'test_id'})

        self.assertEqual(result, {
            'value': 123456,
            'createdAt': time
        })

        self.wrapper.find_one_and_delete.assert_called_once_with(self.collection,
                                                                 filter={'_id': 'test_id'},
                                                                 projection=None,
                                                                 sort=None,
                                                                 fields=Fields(date_times=['createdAt']))

        self.model.fields.assert_called_once_with(None)

    def test_distinct(self):
        self.wrapper.distinct.return_value = {
            'results': self.documents
        }
        self.wrapper.extract = IDatabase.extract
        result = self.model.distinct('_id')

        self.assertEqual(result, self.documents)

        self.wrapper.distinct.assert_called_once_with(self.collection,
                                                      field='_id',
                                                      filter=None,
                                                      fields=None)

    def test_distinct_filter(self):
        self.wrapper.distinct.return_value = {
            'results': self.documents
        }
        self.wrapper.extract = IDatabase.extract
        result = self.model.distinct('_id', filter={'_id': 'test_id'})

        self.assertEqual(result, self.documents)

        self.wrapper.distinct.assert_called_once_with(self.collection,
                                                      field='_id',
                                                      filter={'_id': 'test_id'},
                                                      fields=None)

    def test_distinct_date_time_fields(self):
        self.wrapper.distinct.return_value = {
            'results': self.documents
        }
        self.wrapper.extract = IDatabase.extract
        self.model.date_time_fields = ['test2']
        result = self.model.distinct('_id', fields=Fields(date_times=['test']))

        self.assertEqual(result, self.documents)

        self.wrapper.distinct.assert_called_once_with(self.collection,
                                                      field='_id',
                                                      filter=None,
                                                      fields=Fields(date_times=['test', 'test2']))

    @chainable
    def test_aggregate(self):
        self.wrapper.aggregate.return_value = {
            'cursorId': 1234,
            'alive': False,
            'results': self.documents
        }
        self.wrapper.extract = IDatabase.extract

        self.wrapper.make_cursor = lambda x, fields: IDatabase.make_cursor(self.wrapper, x, fields)
        results = yield self.model.aggregate([{'_id': 'test_id'}])

        self.assertIsInstance(results, Cursor)
        lresults = yield results.to_list()
        self.assertEqual(lresults, self.documents)

        self.wrapper.aggregate.assert_called_once_with(self.collection, pipeline=[{'_id': 'test_id'}])

    @chainable
    def test_delete_one(self):
        self.wrapper.delete_one.return_value = {
            'count': 1
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.delete_one({'_id': 'test_id'})

        self.assertEqual(result, 1)

        self.wrapper.delete_one.assert_called_once_with(self.collection,
                                                        filter={'_id': 'test_id'},
                                                        fields=None)

    @chainable
    def test_delete_one2(self):
        self.wrapper.delete_one.return_value = {
            'count': 1
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.delete_one({'_id': 'test_id'}, fields=Fields(date_times=['test2']))

        self.assertEqual(result, 1)

        self.wrapper.delete_one.assert_called_once_with(self.collection,
                                                        filter={'_id': 'test_id'},
                                                        fields=Fields(date_times=['test2']))

    @chainable
    def test_delete_one_date_time_fields(self):
        self.wrapper.delete_one.return_value = {
            'count': 1
        }
        self.wrapper.extract = IDatabase.extract
        self.model.date_time_fields = ['test']
        result = yield self.model.delete_one({'_id': 'test_id'}, fields=Fields(date_times=['test2']))

        self.assertEqual(result, 1)

        self.wrapper.delete_one.assert_called_once_with(self.collection,
                                                        filter={'_id': 'test_id'},
                                                        fields=Fields(date_times=['test2', 'test']))

    @chainable
    def test_delete_many(self):
        self.wrapper.delete_many.return_value = {
            'count': 2
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.delete_many({'_id': 'test_id'})

        self.assertEqual(result, 2)

        self.wrapper.delete_many.assert_called_once_with(self.collection,
                                                         filter={'_id': 'test_id'},
                                                         fields=None)

    @chainable
    def test_delete_many2(self):
        self.wrapper.delete_many.return_value = {
            'count': 2
        }
        self.wrapper.extract = IDatabase.extract
        result = yield self.model.delete_many({'_id': 'test_id'}, fields=Fields(date_times=['test2']))

        self.assertEqual(result, 2)

        self.wrapper.delete_many.assert_called_once_with(self.collection,
                                                         filter={'_id': 'test_id'},
                                                         fields=Fields(date_times=['test2']))

    @chainable
    def test_delete_many_date_time_fields(self):
        self.wrapper.delete_many.return_value = {
            'count': 2
        }
        self.wrapper.extract = IDatabase.extract
        self.model.date_time_fields = ['test']
        result = yield self.model.delete_many({'_id': 'test_id'}, fields=Fields(date_times=['test2']))

        self.assertEqual(result, 2)

        self.wrapper.delete_many.assert_called_once_with(self.collection,
                                                         filter={'_id': 'test_id'},
                                                         fields=Fields(date_times=['test2', 'test']))

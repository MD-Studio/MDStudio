# coding=utf-8
import unittest
import mock
from autobahn.twisted import ApplicationSession

from mdstudio.db.database import IDatabase
from mdstudio.db.model import Model
from mdstudio.db.response import ReplaceOneResponse, UpdateOneResponse, UpdateManyResponse
from mdstudio.db.session_database import SessionDatabaseWrapper


class ModelTests(unittest.TestCase):

    def setUp(self):
        self.wrapper = mock.MagicMock(spec=SessionDatabaseWrapper)
        self.wrapper.component_info = mock.MagicMock()
        self.wrapper.component_info.get = mock.MagicMock(return_value='namespace')
        self.collection = 'coll'
        self.model = Model(self.wrapper, self.collection)
        self.document = {
            '_id': 'test_id',
            'test': 1234,
            'foo': {
                'bar': False
            }
        }
        self.documents = [self.document, self.document]

    def test_construction(self):

        self.wrapper = mock.Mock()
        self.collection = 'coll'
        self.model = Model(self.wrapper, self.collection)
        self.assertEqual(self.model.wrapper, self.wrapper)

    def test_construction2(self):

        self.assertEquals(self.model.wrapper, self.wrapper)

        self.assertIsInstance(self.model.wrapper, SessionDatabaseWrapper)


    def test_construction3(self):

        self.wrapper = mock.MagicMock(spec=SessionDatabaseWrapper)
        self.wrapper.component_info = mock.MagicMock()
        self.wrapper.component_info.get = mock.MagicMock(return_value='namespace')

        self.model = Model(self.wrapper, self.collection)
        self.assertEquals(self.model.wrapper, self.wrapper)

        self.assertIsInstance(self.model.wrapper, SessionDatabaseWrapper)

    def test_construction4(self):

        self.wrapper = mock.MagicMock(spec=ApplicationSession)
        self.wrapper.component_info = mock.MagicMock()
        self.wrapper.component_info.get = mock.MagicMock(return_value='namespace')

        self.model = Model(self.wrapper, self.collection)
        self.assertNotEquals(self.model.wrapper, self.wrapper)

        self.assertIsInstance(self.model.wrapper, SessionDatabaseWrapper)

    def test_construction_class(self):

        class Users(Model):
            pass

        self.model = Users(self.wrapper)

        self.assertEquals(self.model.collection, 'users')

    def test_insert_one(self):

        self.wrapper.insert_one.return_value = {'id': '12345'}
        self.wrapper.extract = IDatabase.extract
        result = self.model.insert_one(self.document)

        self.assertEquals(result, '12345')

        self.wrapper.insert_one.assert_called_once_with(self.collection, self.document, None)

    def test_insert_one_date_time_fields(self):

        self.wrapper.insert_one.return_value = {'id': '12345'}
        self.wrapper.extract = IDatabase.extract
        result = self.model.insert_one(self.document, ['test'])

        self.assertEquals(result, '12345')

        self.wrapper.insert_one.assert_called_once_with(self.collection, self.document, ['test'])

    def test_insert_one_date_time_fields_inject(self):

        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_one.return_value = {'id': '12345'}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper, self.collection)
        result = self.model.insert_one(self.document, ['test'])

        self.assertEquals(result, '12345')

        self.wrapper.insert_one.assert_called_once_with('users', self.document, ['test', 'datefields'])

    def test_insert_one_date_time_fields_only_inject(self):

        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_one.return_value = {'id': '12345'}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper, self.collection)
        result = self.model.insert_one(self.document)

        self.assertEquals(result, '12345')

        self.wrapper.insert_one.assert_called_once_with('users', self.document, ['datefields'])

    def test_insert_many(self):

        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        result = self.model.insert_many(self.documents)

        self.assertEquals(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with(self.collection, self.documents, None)

    def test_insert_many_date_time_fields(self):

        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        result = self.model.insert_many(self.documents, ['test'])

        self.assertEquals(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with(self.collection, self.documents, ['test'])

    def test_insert_many_date_time_fields_inject(self):

        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper, self.collection)
        result = self.model.insert_many(self.documents, ['test'])

        self.assertEquals(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with('users', self.documents, ['test', 'datefields'])

    def test_insert_many_date_time_fields_only_inject(self):

        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper, self.collection)
        result = self.model.insert_many(self.documents)

        self.assertEquals(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with('users', self.documents, ['datefields'])

    def test_replace_one(self):

        self.wrapper.replace_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        result = self.model.replace_one({'_id': 'test_id'}, self.document)

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEquals(result.matched, 1)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, None)

        self.wrapper.replace_one.assert_called_once_with(self.collection, {'_id': 'test_id'}, self.document, False, None)

    def test_replace_one_upsert(self):

        self.wrapper.replace_one.return_value = {
            'matched': 0,
            'modified': 1,
            'upsertedId': 'test_id2'
        }
        self.wrapper.transform = IDatabase.transform
        result = self.model.replace_one({'_id': 'test_id'}, self.document, upsert=True)

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEquals(result.matched, 0)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, 'test_id2')

        self.wrapper.replace_one.assert_called_once_with(self.collection, {'_id': 'test_id'}, self.document, True, None)

    def test_replace_one_date_time_fields(self):

        self.wrapper.replace_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        result = self.model.replace_one({'_id': 'test_id'}, self.document, date_fields=['test'])

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEquals(result.matched, 1)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, None)

        self.wrapper.replace_one.assert_called_once_with(self.collection, {'_id': 'test_id'}, self.document, False, ['test'])

    def test_replace_one_date_time_fields_inject(self):

        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.replace_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        self.model = Users(self.wrapper, self.collection)
        result = self.model.replace_one({'_id': 'test_id'}, self.document, date_fields=['test'])

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEquals(result.matched, 1)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, None)

        self.wrapper.replace_one.assert_called_once_with('users', {'_id': 'test_id'}, self.document, False, ['test', 'datefields'])

    def test_replace_one_date_time_fields_only_inject(self):

        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.replace_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        self.model = Users(self.wrapper, self.collection)
        result = self.model.replace_one({'_id': 'test_id'}, self.document)

        self.assertIsInstance(result, ReplaceOneResponse)
        self.assertEquals(result.matched, 1)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, None)

        self.wrapper.replace_one.assert_called_once_with('users', {'_id': 'test_id'}, self.document, False, ['datefields'])

    def test_count(self):

        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count()

        self.assertEquals(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection, None, None, None, None, cursor_id=None, with_limit_and_skip=False)

    def test_count_filter(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count({'_id': 'test_id'})

        self.assertEquals(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection, {'_id': 'test_id'}, None, None, None, cursor_id=None, with_limit_and_skip=False)

    def test_count_skip(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count(skip=10)

        self.assertEquals(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection, None, 10, None, None, cursor_id=None, with_limit_and_skip=False)

    def test_count_limit(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count(limit=10)

        self.assertEquals(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection, None, None, 10, None, cursor_id=None, with_limit_and_skip=False)

    def test_count_date_field(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        self.model.date_time_fields = ['test2']
        result = self.model.count(cursor_id='test_id', date_fields=['test'])

        self.assertEquals(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection, None, None, None, ['test', 'test2'], cursor_id='test_id', with_limit_and_skip=False)

    def test_count_cursor_id(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count(cursor_id='test_id')

        self.assertEquals(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection, None, None, None, None, cursor_id='test_id', with_limit_and_skip=False)

    def test_count_cursor_id_with_limit_and_skip(self):
        self.wrapper.count.return_value = {'total': 12345}
        self.wrapper.extract = IDatabase.extract
        result = self.model.count(cursor_id='test_id', with_limit_and_skip=True)

        self.assertEquals(result, 12345)

        self.wrapper.count.assert_called_once_with(self.collection, None, None, None, None, cursor_id='test_id', with_limit_and_skip=True)

    def test_update_one(self):

        self.wrapper.update_one.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        result = self.model.update_one({'_id': 'test_id'}, self.document)

        self.assertIsInstance(result, UpdateOneResponse)
        self.assertEquals(result.matched, 1)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, None)

        self.wrapper.update_one.assert_called_once_with(self.collection, {'_id': 'test_id'}, self.document, False, None)

    def test_update_one_upsert(self):

        self.wrapper.update_one.return_value = {
            'matched': 0,
            'modified': 1,
            'upsertedId': '1234'
        }
        self.wrapper.transform = IDatabase.transform
        result = self.model.update_one({'_id': 'test_id'}, self.document, True)

        self.assertIsInstance(result, UpdateOneResponse)
        self.assertEquals(result.matched, 0)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, '1234')

        self.wrapper.update_one.assert_called_once_with(self.collection, {'_id': 'test_id'}, self.document, True, None)

    def test_update_one_date_fields(self):

        self.wrapper.update_one.return_value = {
            'matched': 0,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        self.model.date_time_fields = ['test2']
        result = self.model.update_one({'_id': 'test_id'}, self.document, date_fields=['test'])

        self.assertIsInstance(result, UpdateOneResponse)
        self.assertEquals(result.matched, 0)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, None)

        self.wrapper.update_one.assert_called_once_with(self.collection, {'_id': 'test_id'}, self.document, False, ['test', 'test2'])


    def test_update_many(self):

        self.wrapper.update_many.return_value = {
            'matched': 1,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        result = self.model.update_many({'_id': 'test_id'}, self.document)

        self.assertIsInstance(result, UpdateManyResponse)
        self.assertEquals(result.matched, 1)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, None)

        self.wrapper.update_many.assert_called_once_with(self.collection, {'_id': 'test_id'}, self.document, False, None)

    def test_update_many_upsert(self):

        self.wrapper.update_many.return_value = {
            'matched': 0,
            'modified': 1,
            'upsertedId': '1234'
        }
        self.wrapper.transform = IDatabase.transform
        result = self.model.update_many({'_id': 'test_id'}, self.document, True)

        self.assertIsInstance(result, UpdateManyResponse)
        self.assertEquals(result.matched, 0)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, '1234')

        self.wrapper.update_many.assert_called_once_with(self.collection, {'_id': 'test_id'}, self.document, True, None)

    def test_update_many_date_fields(self):

        self.wrapper.update_many.return_value = {
            'matched': 0,
            'modified': 1
        }
        self.wrapper.transform = IDatabase.transform
        self.model.date_time_fields = ['test2']
        result = self.model.update_many({'_id': 'test_id'}, self.document, date_fields=['test'])

        self.assertIsInstance(result, UpdateManyResponse)
        self.assertEquals(result.matched, 0)
        self.assertEquals(result.modified, 1)
        self.assertEquals(result.upserted_id, None)

        self.wrapper.update_many.assert_called_once_with(self.collection, {'_id': 'test_id'}, self.document, False, ['test', 'test2'])



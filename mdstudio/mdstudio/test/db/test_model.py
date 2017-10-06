# coding=utf-8
import unittest
import mock
from autobahn.twisted import ApplicationSession

from mdstudio.db.database import IDatabase
from mdstudio.db.model import Model
from mdstudio.db.response import ReplaceOneResponse
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
        result = self.model.insert_many(self.document)

        self.assertEquals(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with(self.collection, self.document, None)

    def test_insert_many_date_time_fields(self):

        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        result = self.model.insert_many(self.document, ['test'])

        self.assertEquals(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with(self.collection, self.document, ['test'])

    def test_insert_many_date_time_fields_inject(self):

        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper, self.collection)
        result = self.model.insert_many(self.document, ['test'])

        self.assertEquals(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with('users', self.document, ['test', 'datefields'])

    def test_insert_many_date_time_fields_only_inject(self):

        class Users(Model):
            date_time_fields = ['datefields']

        self.wrapper.insert_many.return_value = {'ids': ['12345', '456789']}
        self.wrapper.extract = IDatabase.extract
        self.model = Users(self.wrapper, self.collection)
        result = self.model.insert_many(self.document)

        self.assertEquals(result, ['12345', '456789'])

        self.wrapper.insert_many.assert_called_once_with('users', self.document, ['datefields'])

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

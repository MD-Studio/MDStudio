# coding=utf-8

from mock import mock
from twisted.internet.defer import Deferred
from twisted.trial.unittest import TestCase

from mdstudio.db.cursor import Cursor
from mdstudio.db.fields import Fields
from mdstudio.db.session_database import SessionDatabaseWrapper
from mdstudio.db.sort_mode import SortMode
from mdstudio.deferred.chainable import chainable


class SessionDatabaseWrapperTests(TestCase):
    def setUp(self):
        self.session = mock.Mock()
        self.session.call = mock.MagicMock(return_value='namespace')

        self.wrapper = SessionDatabaseWrapper(self.session)

    def test_construction(self):
        self.assertIsInstance(self.wrapper, SessionDatabaseWrapper)
        self.assertEqual(self.wrapper.session, self.session)

    def test_more(self):
        self.wrapper.more('123456')

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.more', {
            'cursorId': '123456'
        }, claims={'connectionType': 'user'})

    def test_rewind(self):
        self.wrapper.rewind('123456')

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.rewind', {
            'cursorId': '123456'
        }, claims={'connectionType': 'user'})

    def test_insert_one(self):
        self.wrapper.insert_one('col', {'test': 8})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.insert_one', {
            'collection': 'col',
            'insert': {'test': 8}
        }, claims={'connectionType': 'user'})

    def test_insert_one_date_time_fields(self):
        self.wrapper.insert_one('col', {'test': 8}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.insert_one', {
            'collection': 'col',
            'insert': {'test': 8},
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_insert_many(self):
        self.wrapper.insert_many('col', [{'test': 8}, {'test4': 4}])

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.insert_many', {
            'collection': 'col',
            'insert': [{'test': 8}, {'test4': 4}]
        }, claims={'connectionType': 'user'})

    def test_insert_many_date_time_fields(self):
        self.wrapper.insert_many('col', [{'test': 8}, {'test4': 4}], fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.insert_many', {
            'collection': 'col',
            'insert': [{'test': 8}, {'test4': 4}],
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_replace_one(self):
        self.wrapper.replace_one('col', {'_id': 5}, {'test': 8})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.replace_one', {
            'collection': 'col',
            'filter': {'_id': 5},
            'replacement': {'test': 8},
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_replace_one_upsert(self):
        self.wrapper.replace_one('col', {'_id': 5}, {'test': 8}, upsert=True)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.replace_one', {
            'collection': 'col',
            'filter': {'_id': 5},
            'replacement': {'test': 8},
            'upsert': True
        }, claims={'connectionType': 'user'})

    def test_replace_one_date_time_fields(self):
        self.wrapper.replace_one('col', {'_id': 5}, {'test': 8}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.replace_one', {
            'collection': 'col',
            'filter': {'_id': 5},
            'replacement': {'test': 8},
            'upsert': False,
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_count(self):
        self.wrapper.count('col')

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.count', {
            'collection': 'col'
        }, claims={'connectionType': 'user'})

    def test_count_cursor_id(self):
        self.wrapper.count('col', cursor_id='1234')

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.count', {
            'collection': 'col',
            'cursorId': '1234'
        }, claims={'connectionType': 'user'})

    def test_count_cursor_id_with_skip_and_limit(self):
        self.wrapper.count('col', cursor_id='1234', with_limit_and_skip=True)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.count', {
            'collection': 'col',
            'cursorId': '1234',
            'withLimitAndSkip': True
        }, claims={'connectionType': 'user'})

    def test_count_with_skip_and_limit(self):
        self.wrapper.count('col', with_limit_and_skip=True)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.count', {
            'collection': 'col'
        }, claims={'connectionType': 'user'})

    def test_count_filter(self):
        self.wrapper.count('col', filter={'_id': 5})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.count', {
            'collection': 'col',
            'filter': {'_id': 5}
        }, claims={'connectionType': 'user'})

    def test_count_skip(self):
        self.wrapper.count('col', skip=10)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.count', {
            'collection': 'col',
            'skip': 10
        }, claims={'connectionType': 'user'})

    def test_count_limit(self):
        self.wrapper.count('col', limit=10)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.count', {
            'collection': 'col',
            'limit': 10
        }, claims={'connectionType': 'user'})

    def test_count_date_time_fields(self):
        self.wrapper.count('col', fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.count', {
            'collection': 'col',
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_update_one(self):
        self.wrapper.update_one('col', {'_id': 50}, {'test': 11})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.update_one', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 11}
        }, claims={'connectionType': 'user'})

    def test_update_one_upsert(self):
        self.wrapper.update_one('col', {'_id': 50}, {'test': 11}, upsert=True)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.update_one', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 11},
            'upsert': True
        }, claims={'connectionType': 'user'})

    def test_update_one_date_time_fields(self):
        self.wrapper.update_one('col', {'_id': 50}, {'test': 11}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.update_one', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 11},
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_update_many(self):
        self.wrapper.update_many('col', {'_id': 50}, {'test': 11})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.update_many', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 11}
        }, claims={'connectionType': 'user'})

    def test_update_many_upsert(self):
        self.wrapper.update_many('col', {'_id': 50}, {'test': 11}, upsert=True)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.update_many', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 11},
            'upsert': True
        }, claims={'connectionType': 'user'})

    def test_update_many_date_time_fields(self):
        self.wrapper.update_many('col', {'_id': 50}, {'test': 11}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.update_many', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 11},
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_find_one(self):
        self.wrapper.find_one('col', {'_id': 50})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one', {
            'collection': 'col',
            'filter': {'_id': 50}
        }, claims={'connectionType': 'user'})

    def test_find_one_projection(self):
        self.wrapper.find_one('col', {'_id': 50}, projection={'projection': 'yes'})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one', {
            'collection': 'col',
            'filter': {'_id': 50},
            'projection': {'projection': 'yes'}
        }, claims={'connectionType': 'user'})

    def test_find_one_skip(self):
        self.wrapper.find_one('col', {'_id': 50}, skip=10)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one', {
            'collection': 'col',
            'filter': {'_id': 50},
            'skip': 10
        }, claims={'connectionType': 'user'})

    def test_find_one_sort(self):
        self.wrapper.find_one('col', {'_id': 50}, sort=[('_id', SortMode.Asc)])

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one', {
            'collection': 'col',
            'filter': {'_id': 50},
            'sort': [('_id', SortMode.Asc)]
        }, claims={'connectionType': 'user'})

    def test_find_one_date_time(self):
        self.wrapper.find_one('col', {'_id': 50}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one', {
            'collection': 'col',
            'filter': {'_id': 50},
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_find_many(self):
        self.wrapper.find_many('col', {'_id': 50})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_many', {
            'collection': 'col',
            'filter': {'_id': 50}
        }, claims={'connectionType': 'user'})

    def test_find_many_projection(self):
        self.wrapper.find_many('col', {'_id': 50}, projection={'projection': 'yes'})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_many', {
            'collection': 'col',
            'filter': {'_id': 50},
            'projection': {'projection': 'yes'}
        }, claims={'connectionType': 'user'})

    def test_find_many_skip(self):
        self.wrapper.find_many('col', {'_id': 50}, skip=10)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_many', {
            'collection': 'col',
            'filter': {'_id': 50},
            'skip': 10
        }, claims={'connectionType': 'user'})

    def test_find_many_limit(self):
        self.wrapper.find_many('col', {'_id': 50}, limit=10)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_many', {
            'collection': 'col',
            'filter': {'_id': 50},
            'limit': 10
        }, claims={'connectionType': 'user'})

    def test_find_many_sort(self):
        self.wrapper.find_many('col', {'_id': 50}, sort=[('_id', SortMode.Asc)])

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_many', {
            'collection': 'col',
            'filter': {'_id': 50},
            'sort': [('_id', SortMode.Asc)]
        }, claims={'connectionType': 'user'})

    def test_find_many_date_time(self):
        self.wrapper.find_many('col', {'_id': 50}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_many', {
            'collection': 'col',
            'filter': {'_id': 50},
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_find_one_and_update(self):
        self.wrapper.find_one_and_update('col', {'_id': 50}, {'test': 80})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_update', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 80},
            'returnUpdated': False,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_update_upsert(self):
        self.wrapper.find_one_and_update('col', {'_id': 50}, {'test': 80}, upsert=True)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_update', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 80},
            'returnUpdated': False,
            'upsert': True
        }, claims={'connectionType': 'user'})

    def test_find_one_and_update_return_updated(self):
        self.wrapper.find_one_and_update('col', {'_id': 50}, {'test': 80}, return_updated=True)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_update', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 80},
            'returnUpdated': True,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_update_date_time_fields(self):
        self.wrapper.find_one_and_update('col', {'_id': 50}, {'test': 80}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_update', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 80},
            'fields': {
                'datetime': ['field1', 'field2']
            },
            'returnUpdated': False,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_update_projection(self):
        self.wrapper.find_one_and_update('col', {'_id': 50}, {'test': 80}, projection={'projection': 'yes'})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_update', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 80},
            'projection': {'projection': 'yes'},
            'returnUpdated': False,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_update_sort(self):
        self.wrapper.find_one_and_update('col', {'_id': 50}, {'test': 80}, sort=[('_id', SortMode.Asc)])

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_update', {
            'collection': 'col',
            'filter': {'_id': 50},
            'update': {'test': 80},
            'sort': [('_id', SortMode.Asc)],
            'returnUpdated': False,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_replace(self):
        self.wrapper.find_one_and_replace('col', {'_id': 50}, {'test': 80})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_replace', {
            'collection': 'col',
            'filter': {'_id': 50},
            'replacement': {'test': 80},
            'returnUpdated': False,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_replace_upsert(self):
        self.wrapper.find_one_and_replace('col', {'_id': 50}, {'test': 80}, upsert=True)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_replace', {
            'collection': 'col',
            'filter': {'_id': 50},
            'replacement': {'test': 80},
            'returnUpdated': False,
            'upsert': True
        }, claims={'connectionType': 'user'})

    def test_find_one_and_replace_return_updated(self):
        self.wrapper.find_one_and_replace('col', {'_id': 50}, {'test': 80}, return_updated=True)

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_replace', {
            'collection': 'col',
            'filter': {'_id': 50},
            'replacement': {'test': 80},
            'returnUpdated': True,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_replace_date_time_fields(self):
        self.wrapper.find_one_and_replace('col', {'_id': 50}, {'test': 80}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_replace', {
            'collection': 'col',
            'filter': {'_id': 50},
            'replacement': {'test': 80},
            'fields': {
                'datetime': ['field1', 'field2']
            },
            'returnUpdated': False,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_replace_projection(self):
        self.wrapper.find_one_and_replace('col', {'_id': 50}, {'test': 80}, projection={'projection': 'yes'})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_replace', {
            'collection': 'col',
            'filter': {'_id': 50},
            'replacement': {'test': 80},
            'projection': {'projection': 'yes'},
            'returnUpdated': False,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_replace_sort(self):
        self.wrapper.find_one_and_replace('col', {'_id': 50}, {'test': 80}, sort=[('_id', SortMode.Asc)])

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_replace', {
            'collection': 'col',
            'filter': {'_id': 50},
            'replacement': {'test': 80},
            'sort': [('_id', SortMode.Asc)],
            'returnUpdated': False,
            'upsert': False
        }, claims={'connectionType': 'user'})

    def test_find_one_and_delete(self):
        self.wrapper.find_one_and_delete('col', {'_id': 50})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_delete', {
            'collection': 'col',
            'filter': {'_id': 50},
        }, claims={'connectionType': 'user'})

    def test_find_one_and_delete_projection(self):
        self.wrapper.find_one_and_delete('col', {'_id': 50}, projection={'projection': 'yes'})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_delete', {
            'collection': 'col',
            'filter': {'_id': 50},
            'projection': {'projection': 'yes'},
        }, claims={'connectionType': 'user'})

    def test_find_one_and_delete_sort(self):
        self.wrapper.find_one_and_delete('col', {'_id': 50}, sort=[('_id', SortMode.Asc)])

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_delete', {
            'collection': 'col',
            'filter': {'_id': 50},
            'sort': [('_id', SortMode.Asc)],
        }, claims={'connectionType': 'user'})

    def test_find_one_and_delete_date_time(self):
        self.wrapper.find_one_and_delete('col', {'_id': 50}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.find_one_and_delete', {
            'collection': 'col',
            'filter': {'_id': 50},
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_distinct(self):
        self.wrapper.distinct('col', '_id')

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.distinct', {
            'collection': 'col',
            'field': '_id'
        }, claims={'connectionType': 'user'})

    def test_distinct_query(self):
        self.wrapper.distinct('col', '_id', {'_id': 5})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.distinct', {
            'collection': 'col',
            'field': '_id',
            'query': {'_id': 5}
        }, claims={'connectionType': 'user'})

    def test_distinct_date_time(self):
        self.wrapper.distinct('col', '_id', fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.distinct', {
            'collection': 'col',
            'field': '_id',
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_aggregate(self):
        self.wrapper.aggregate('col', [{'test': 10}])

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.aggregate', {
            'collection': 'col',
            'pipeline': [{'test': 10}]
        }, claims={'connectionType': 'user'})

    def test_delete_one(self):
        self.wrapper.delete_one('col', {'test': 10})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.delete_one', {
            'collection': 'col',
            'filter': {'test': 10}
        }, claims={'connectionType': 'user'})

    def test_delete_one_date_time_fields(self):
        self.wrapper.delete_one('col', {'test': 10}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.delete_one', {
            'collection': 'col',
            'filter': {'test': 10},
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})

    def test_delete_many(self):
        self.wrapper.delete_many('col', {'test': 10})

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.delete_many', {
            'collection': 'col',
            'filter': {'test': 10}
        }, claims={'connectionType': 'user'})

    def test_delete_many_date_time_fields(self):
        self.wrapper.delete_many('col', {'test': 10}, fields=Fields(date_times=['field1', 'field2']))

        self.session.call.assert_called_once_with('mdstudio.db.endpoint.delete_many', {
            'collection': 'col',
            'filter': {'test': 10},
            'fields': {
                'datetime': ['field1', 'field2']
            }
        }, claims={'connectionType': 'user'})


# noinspection PyPep8
class TestSessionDatabaseWrapperDeferred(TestCase):
    def test_extract(self):
        d = {
            'test': 2,
            'test2': 3
        }

        self.assertEqual(SessionDatabaseWrapper.extract(d, 'test'), 2)

    @chainable
    def test_transform(self):
        identity = lambda x: x
        const = lambda x: 2
        self.assertEqual((yield SessionDatabaseWrapper.transform(None, identity)), None)
        self.assertEqual((yield SessionDatabaseWrapper.transform(None, const)), None)
        self.assertEqual((yield SessionDatabaseWrapper.transform(4, const)), 2)
        self.assertEqual((yield SessionDatabaseWrapper.transform(3, identity)), 3)
        self.assertEqual((yield SessionDatabaseWrapper.transform(2, lambda x: x ** 2)), 4)
        self.assertEqual((yield SessionDatabaseWrapper.transform('test', identity)), 'test')

    @chainable
    def test_make_cursor(self):
        documents = [
            {
                'test': False
            },
            {
                'test': True
            }
        ]
        d = {
            'cursorId': 1234,
            'alive': False,
            'results': documents
        }

        db = SessionDatabaseWrapper(mock.MagicMock())
        db.make_cursor(d, Fields()).addCallback(self.assertIsInstance, Cursor)
        self.assertIsInstance(db.make_cursor(d, Fields()), Deferred)

        docs = yield db.make_cursor(d, Fields()).to_list()

        self.assertEqual(docs, documents)

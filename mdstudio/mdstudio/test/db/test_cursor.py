# coding=utf-8
import unittest
import mock

from mdstudio.db.cursor import Cursor


class CursorTests(unittest.TestCase):

    def setUp(self):
        self.wrapper = mock.Mock()
        self.values = [
            {'test': 5},
            {'test2': 2}
        ]
        self.cursor = Cursor(self.wrapper, {
            '_id': 1234,
            'alive': True,
            'result': self.values
        })

    def test_construction(self):

        self.assertEqual(self.cursor._id, 1234)
        self.assertEqual(self.cursor._alive, True)
        self.assertEqual(len(self.cursor._data), 2)

    def test_next(self):

        self.assertEqual(next(self.cursor), {'test': 5})
        self.assertEqual(next(self.cursor), {'test2': 2})

    def test_iter_stop(self):

        self.wrapper.more = mock.MagicMock(return_value={'_id': 1234, 'alive': False, 'result': []})
        for i, v in enumerate(self.cursor):
            self.assertEqual(v, self.values[i])

        self.wrapper.more.assert_called_with(**{'cursor_id':1234})

    def test_more(self):

        nxt = lambda: next(self.cursor)
        self.assertEqual(nxt(), {'test': 5})
        self.assertEqual(nxt(), {'test2': 2})

        self.wrapper.more = mock.MagicMock(return_value={'_id': 1234, 'alive': True, 'result': [{'test3': 8}]})
        self.assertEqual(nxt(), {'test3': 8})

        self.wrapper.more = mock.MagicMock(return_value={'_id': 1234, 'alive': False, 'result': [{'test6': 2}]})
        self.assertEqual(nxt(), {'test6': 2})

        self.assertRaises(StopIteration, nxt)

    def test_id(self):

        nxt = lambda: next(self.cursor)
        self.assertEqual(nxt(), {'test': 5})
        self.assertEqual(nxt(), {'test2': 2})

        self.wrapper.more = mock.MagicMock(return_value={'_id': 1244, 'alive': True, 'result': [{'test3': 8}]})
        self.assertEqual(nxt(), {'test3': 8})

        self.wrapper.more.assert_called_with(**{'cursor_id':1234})

        self.wrapper.more = mock.MagicMock(return_value={'_id': 1234, 'alive': False, 'result': [{'test6': 2}]})
        self.assertEqual(nxt(), {'test6': 2})

        self.wrapper.more.assert_called_with(**{'cursor_id':1244})

        self.assertRaises(StopIteration, nxt)

    def test_foreach(self):

        hist = {'test': 0, 'test2': 0}

        def test(o):
            for k, v in o.items():
                hist[k] += v

        self.wrapper.more = mock.MagicMock(return_value={'_id': 1234, 'alive': False, 'result': []})
        self.cursor.for_each(test)

        self.assertEqual(hist['test'], 5)
        self.assertEqual(hist['test2'], 2)

    def test_query(self):

        hist = {'test': 0, 'test2': 0}

        def test(o):
            for k, v in o.items():
                hist[k] += v

        self.wrapper.more = mock.MagicMock(return_value={'_id': 1234, 'alive': False, 'result': []})
        results = self.cursor.query().select(lambda x: True if 'test' in x else False).to_list()

        self.assertEqual(len(results), 2)
        self.assertEqual(results, [True, False])

    def test_count(self):

        self.wrapper.count = mock.MagicMock(return_value=2)
        self.assertEqual(self.cursor.count(), 2)
        self.wrapper.count.assert_called_with(**{'cursor_id': 1234, 'with_limit_and_skip': False})

    def test_count2(self):

        self.wrapper.count = mock.MagicMock(return_value=2)
        self.assertEqual(self.cursor.count(True), 2)
        self.wrapper.count.assert_called_with(**{'cursor_id': 1234, 'with_limit_and_skip': True})
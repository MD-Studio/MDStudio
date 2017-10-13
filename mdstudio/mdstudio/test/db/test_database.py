# coding=utf-8
import unittest
import mock

from mdstudio.db.database import IDatabase


class DatabaseTests(unittest.TestCase):
    @mock.patch.multiple(IDatabase, __abstractmethods__=set())
    def test_transform(self):
        db = IDatabase()
        identity = lambda x: x
        const = lambda x: 2
        self.assertEqual(db.transform(None, identity), None)
        self.assertEqual(db.transform(None, const), None)
        self.assertEqual(db.transform(4, const), 2)
        self.assertEqual(db.transform(3, identity), 3)
        self.assertEqual(db.transform(2, lambda x: x ** 2), 4)
        self.assertEqual(db.transform('test', identity), 'test')

    @mock.patch.multiple(IDatabase, __abstractmethods__=set())
    def test_extract(self):
        db = IDatabase()
        d = {
            'test': 2,
            'test2': 3
        }
        self.assertEqual(db.extract(d, 'test'), 2)
        self.assertEqual(db.extract(d, 'test2'), 3)

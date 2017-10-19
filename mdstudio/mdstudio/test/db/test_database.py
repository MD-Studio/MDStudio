# coding=utf-8
import unittest
import mock

from mdstudio.db.database import IDatabase
from mdstudio.deferred.chainable import chainable


class DatabaseTests(unittest.TestCase):
    @mock.patch.multiple(IDatabase, __abstractmethods__=set())
    @chainable
    def test_transform(self):
        db = IDatabase()
        identity = lambda x: x
        const = lambda x: 2
        self.assertEqual((yield db.transform(None, identity)), None)
        self.assertEqual((yield db.transform(None, const)), None)
        self.assertEqual((yield db.transform(4, const)), 2)
        self.assertEqual((yield db.transform(3, identity)), 3)
        self.assertEqual((yield db.transform(2, lambda x: x ** 2)), 4)
        self.assertEqual((yield db.transform('test', identity)), 'test')

    @mock.patch.multiple(IDatabase, __abstractmethods__=set())
    def test_extract(self):
        db = IDatabase()
        d = {
            'test': 2,
            'test2': 3
        }
        self.assertEqual(db.extract(d, 'test'), 2)
        self.assertEqual(db.extract(d, 'test2'), 3)

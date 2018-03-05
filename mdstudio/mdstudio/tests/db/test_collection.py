# coding=utf-8
import unittest

from mdstudio.db.collection import Collection


class CollectionTests(unittest.TestCase):
    def test_default(self):
        col = Collection('name', 'namespace')
        self.assertIsInstance(col, dict)
        self.assertEqual(col.name, 'name')
        self.assertEqual(col.namespace, 'namespace')

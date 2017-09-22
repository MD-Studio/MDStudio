# coding=utf-8
import unittest

from mdstudio.db.response import UpdateManyResponse, UpdateOneResponse, ReplaceOneResponse


class ResponseTests(unittest.TestCase):

    def test_UpdateManyResponse(self):
        many = UpdateManyResponse({
            'matched': 2,
            'modified': 1,
            'upsertedId': '234'
        })
        self.assertEqual(many.matched_count, 2)
        self.assertEqual(many.modified_count, 1)
        self.assertEqual(many.upserted_id, '234')

    def test_UpdateOneResponse(self):
        many = UpdateOneResponse({
            'matched': 2,
            'modified': 1,
            'upsertedId': '234'
        })
        self.assertEqual(many.matched_count, 2)
        self.assertEqual(many.modified_count, 1)
        self.assertEqual(many.upserted_id, '234')

    def test_ReplaceOneResponse(self):
        many = ReplaceOneResponse({
            'matched': 2,
            'modified': 1,
            'upsertedId': '234'
        })
        self.assertEqual(many.matched_count, 2)
        self.assertEqual(many.modified_count, 1)
        self.assertEqual(many.upserted_id, '234')
# coding=utf-8
import unittest

from mdstudio.db.sort_mode import SortMode


class SortModeTests(unittest.TestCase):

    def test_asc(self):
        self.assertEqual(str(SortMode.Asc), "asc")

    def test_desc(self):
        self.assertEqual(str(SortMode.Desc), "desc")

    def test_neq(self):
        self.assertNotEquals(SortMode.Desc, SortMode.Asc)
from collections import OrderedDict
from unittest import TestCase

from mdstudio.collection import merge_dicts


class TestCollection(TestCase):
    def test_merge(self):
        a = {'a': 4}
        b = {'b': 5}
        merge_dicts(a, b)
        self.assertEqual(a, {
            'a': 4,
            'b': 5
        })
        self.assertEqual(b, {'b': 5})

    def test_merge2(self):
        a = {'a': 4}
        b = {
            'a': 6,
            'b': 5
        }
        merge_dicts(a, b)
        self.assertEqual(a, {
            'a': 6,
            'b': 5
        })

    def test_merge3(self):
        a = {'a': 4}
        b = OrderedDict([
            ('a', 6),
            ('b', 5)
        ])
        merge_dicts(a, b)
        self.assertEqual(a, {
            'a': 6,
            'b': 5
        })

    def test_merge4(self):
        a = {'a': 4, 'b': {'c': 4}}
        b = {
            'a': 6,
            'b': 5
        }
        merge_dicts(a, b)
        self.assertEqual(a, {
            'a': 6,
            'b': 5
        })

    def test_merge5(self):
        a = {'a': 4}
        b = {
            'a': 6,
            'b': {'c': 4}
        }
        merge_dicts(a, b)
        self.assertEqual(a, {
            'a': 6,
            'b': {'c': 4}
        })

    def test_merge6(self):
        a = {'a': 4, 'b': {'c': 10}}
        b = {
            'a': 6,
            'b': {'c': 4}
        }
        merge_dicts(a, b)
        self.assertEqual(a, {
            'a': 6,
            'b': {'c': 4}
        })

from time import sleep

from twisted.trial.unittest import TestCase

from mdstudio.collection.cache_dict import CacheDict


class TestCacheDict(TestCase):
    def setUp(self):
        self.d = CacheDict(1)

    def test_construct(self):
        self.assertEqual(self.d.max_age, 1)

    def test_construct_assert(self):
        with self.assertRaises(AssertionError):
            CacheDict(-1)

    def test_empty_contains(self):
        self.assertFalse('test' in self.d)

    def test_expiry(self):
        self.d['test'] = 1
        self.d['test2'] = 2

        self.assertTrue('test' in self.d)
        self.assertTrue('test2' in self.d)

        self.assertEqual(self.d['test'], 1)
        self.assertEqual(self.d['test2'], 2)

        sleep(1)

        self.assertFalse('test' in self.d)
        self.assertFalse('test2' in self.d)

    def test_expiry2(self):
        self.d['test'] = 1
        self.d['test2'] = 2

        self.assertEqual(self.d['test'], 1)
        self.assertEqual(self.d['test2'], 2)

        sleep(1)

        with self.assertRaises(KeyError):
            _ = self.d['test']
        with self.assertRaises(KeyError):
            _ = self.d['test2']

    def test_expiry_reset(self):
        self.d = CacheDict(2)

        self.d['test'] = 1
        self.d['test2'] = 2

        self.assertEqual(self.d['test'], 1)
        self.assertEqual(self.d['test2'], 2)

        sleep(1)

        self.assertEqual(self.d['test'], 1)
        self.assertEqual(self.d['test2'], 2)

        self.d['test'] = 5
        self.d['test2'] = 6

        self.assertEqual(self.d['test'], 5)
        self.assertEqual(self.d['test2'], 6)

        sleep(1)

        self.assertEqual(self.d['test'], 5)
        self.assertEqual(self.d['test2'], 6)

        sleep(1)

        self.assertFalse('test' in self.d)
        self.assertFalse('test2' in self.d)

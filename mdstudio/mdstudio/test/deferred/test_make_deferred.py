from twisted.internet.defer import Deferred
from twisted.trial.unittest import TestCase

from mdstudio.deferred.make_deferred import make_deferred


class TestMakeDeferred(TestCase):

    def test_no_args(self):

        class Test:

            @make_deferred
            def test(self):
                return 3

        test = Test()
        test.test().addCallback(self.assertIsInstance, Deferred)
        self.assertIsInstance(test.test(), Deferred)

        test.test().addCallback(self.assertEqual, 3)

    def test_args(self):

        class Test:

            @make_deferred
            def add(self, a, b):
                return a + b

        test = Test()
        test.add(1, 5).addCallback(self.assertIsInstance, Deferred)
        self.assertIsInstance(test.add(6, 9), Deferred)

        test.add(12,3).addCallback(self.assertEqual, 15)

    def test_kwargs(self):

        class Test:

            @make_deferred
            def add(self, a, b):
                return a + b

        test = Test()

        test.add(**{'a':12, 'b':3}).addCallback(self.assertEqual, 15)
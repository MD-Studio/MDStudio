from twisted.internet.defer import Deferred
from twisted.trial.unittest import TestCase

from mdstudio.deferred.deferred_wrapper import DeferredWrapper
from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.deferred.chainable import nonblocking
from mdstudio.deferred.return_value import return_value


class NonBlockingTestClass:
    def __init__(self, inst):
        self.inst = inst

    @make_deferred
    def test(self):
        return 3

    @nonblocking
    def call(self):
        value = yield self.test()
        return_value(value)

    @nonblocking
    def call2(self):
        value = yield self.call()
        return_value(value)

    def call3(self):
        return self.call2()

    def assertEquals(self, val):
        self.inst.assertEquals(val)


class TestNonBlocking(TestCase):
    def test_basic_deferred(self):
        test = NonBlockingTestClass(self)
        test.call().addCallback(self.assertIsInstance, Deferred)
        test.call().addCallback(self.assertIsInstance, DeferredWrapper)
        self.assertIsInstance(test.call(), Deferred)
        self.assertIsInstance(test.call(), DeferredWrapper)

        test.call().addCallback(self.assertEquals, 3)

    def test_chained(self):
        test = NonBlockingTestClass(self)
        test.call().assertEquals(3)
        test.call2().assertEquals(3)
        test.call3().assertEquals(3)

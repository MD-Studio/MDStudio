from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.trial.unittest import TestCase
from twisted.internet import reactor, threads
import threading
import twisted

# import sys

# from twisted.python import log



# log.startLogging(sys.stdout)

from mdstudio.deferred.deferred_wrapper import DeferredWrapper
from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value

twisted.internet.base.DelayedCall.debug = True

class ChainedObject:
    def __init__(self, deferred):
        self.deferred = deferred

    @chainable
    def chained_call(self):
        res = yield self.deferred
        return_value({'test': res})

class TestableResult:
    def __init__(self, inst, result):
        self.inst = inst
        self.value = result

    def assertEqual(self, val):
        self.inst.assertEqual(val, self.value)

class ChainableTestClass:
    def __init__(self, inst):
        self.inst = inst

    # @make_deferred
    def test(self):
        return TestableResult(self.inst, 3)

    @chainable
    def call(self):
        value = yield self.test()
        return_value(value)

    @chainable
    def call2(self):
        value = yield self.call()
        return_value(value)

    def call3(self):
        return self.call2()

    @chainable
    def initial_call(self, deferred):
        res = yield deferred.chained_call()['test']

        return_value(TestableResult(self.inst, res))

    def assertEqual(self, val):
        self.inst.assertEqual(val)

class TestChainable(TestCase):
    def test_basic_deferred(self):
        test = ChainableTestClass(self)
        self.assertIsInstance(test.call(), Deferred)
        self.assertIsInstance(test.call(), DeferredWrapper)
        test.call().value.addCallback(self.assertIsInstance, int)

        return test.call().assertEqual(3)

    def test_chained(self):
        test = ChainableTestClass(self)

        @chainable
        def test_all():
            test1 = yield test.call().assertEqual(3)
            test2 = yield test.call2().assertEqual(3)
            test3 = yield test.call3().assertEqual(3)
            return_value(test3)

        return test_all()

    def test_deferred_chain(self):
        d = Deferred()
        d2 = Deferred()

        test = ChainableTestClass(self)
        result = test.initial_call(DeferredWrapper(d))

        # result = initial_call(DeferredWrapper(d))
        d.callback(ChainedObject(d2))
        d2.callback(42)
        result.assertEqual(42)

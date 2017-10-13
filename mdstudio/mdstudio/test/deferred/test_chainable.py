from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.trial.unittest import TestCase
from twisted.internet import reactor
import twisted

import sys

from twisted.python import log



log.startLogging(sys.stdout)

from mdstudio.deferred.deferred_wrapper import DeferredWrapper
from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value

twisted.internet.base.DelayedCall.debug = True

class ChainableTestClass:
    def __init__(self, inst):
        self.inst = inst

    @make_deferred
    def test(self):
        return 3

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

    def assertEqual(self, val):
        self.inst.assertEqual(val)


class TestDeferredChain(TestCase):
    def test_basic_chain(self):
        class ChainedObject:
            @inlineCallbacks
            def chained_call(self):
                # res = yield d2
                res = yield 2
                # print('received d2')
                return_value({'test': 42})

        @inlineCallbacks
        def initial_call(deferred):
            # print(deferred)
            # reactor.callLater(1, d2.callback, {})
            res = yield deferred.chained_call().get('test')
            d3.callback({})
            return_value(res)

        d = Deferred()
        d2 = Deferred()
        d3 = Deferred()
        reactor.callLater(2, d.callback, ChainedObject())
        reactor.callWhenRunning(initial_call, DeferredWrapper(d))

        return d3


class TestChainable(TestCase):
    def test_basic_deferred(self):
        test = ChainableTestClass(self)
        test.call().addCallback(self.assertIsInstance, Deferred)
        test.call().addCallback(self.assertIsInstance, DeferredWrapper)
        self.assertIsInstance(test.call(), Deferred)
        self.assertIsInstance(test.call(), DeferredWrapper)

        test.call().addCallback(self.assertEquals, 3)

    def test_chained(self):
        test = ChainableTestClass(self)
        test.call().assertEqual(3)
        test.call2().assertEqual(3)
        test.call3().assertEqual(3)

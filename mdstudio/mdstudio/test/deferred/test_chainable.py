import twisted
from twisted.internet.defer import Deferred
from twisted.trial.unittest import TestCase

from mdstudio.deferred.chainable import Chainable
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


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
        self.assertIsInstance(test.call(), Chainable)
        test.call().value.addCallback(self.assertIsInstance, int)

        return test.call().assertEqual(3)

    def test_chained(self):
        test = ChainableTestClass(self)

        @chainable
        def test_all():
            yield test.call().assertEqual(3)
            yield test.call2().assertEqual(3)
            test3 = yield test.call3().assertEqual(3)
            return_value(test3)

        return test_all()

    def test_deferred_chain(self):
        d = Deferred()
        d2 = Deferred()

        test = ChainableTestClass(self)
        result = test.initial_call(Chainable(d))

        d.callback(ChainedObject(d2))
        d2.callback(42)
        result.assertEqual(42)

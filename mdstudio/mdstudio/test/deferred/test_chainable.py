import twisted
from twisted.internet.defer import Deferred
from twisted.trial.unittest import TestCase
from twisted.internet import reactor

from mdstudio.deferred.chainable import Chainable, chainable
from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.deferred.return_value import return_value
from mdstudio.unittest import wait_for_completion


class ChainedObject:
    def __init__(self, deferred):
        self.deferred = deferred

    @chainable
    def chained_call(self):
        res = yield self.deferred
        return_value({'test': res})


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

    @chainable
    def initial_call(self, deferred):
        res = yield deferred.chained_call()['test']

        return_value(res)


class TestChainable(TestCase):
    def setUp(self):
        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

        wait_for_completion.wait_for_completion = True

    def tearDown(self):
        wait_for_completion.wait_for_completion = False

    @chainable
    def test_basic_deferred(self):
        test = ChainableTestClass(self)
        d = test.call()
        self.assertIsInstance(d, Deferred)
        self.assertIsInstance(d, Chainable)
        self.assertIsInstance((yield d), int)
        self.assertEqual((yield test.call()), 3)

    @chainable
    def test_chained(self):
        test = ChainableTestClass(self)

        self.assertEqual((yield test.call()), 3)
        self.assertEqual((yield test.call2()), 3)
        self.assertEqual((yield test.call3()), 3)

    @chainable
    def test_deferred_chain(self):
        d = Deferred()
        d2 = Deferred()

        test = ChainableTestClass(self)
        result = test.initial_call(Chainable(d))

        d.callback(ChainedObject(d2))
        d2.callback(42)
        self.assertEqual((yield result), 42)

from twisted.internet import reactor
from twisted.trial.unittest import TestCase

from mdstudio.deferred.chainable import test_chainable, Chainable
from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.deferred.return_value import return_value


class TestMakeDeferred(TestCase):
    def setUp(self):
        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

    @test_chainable
    def test_no_args(self):
        class Test:
            @make_deferred
            def test(self):
                return 3

        test = Test()

        testTest = test.test()
        self.assertIsInstance(testTest, Chainable)
        self.assertEqual(3, (yield testTest))

        return_value({})

    @test_chainable
    def test_args(self):
        class Test:
            @make_deferred
            def add(self, a, b):
                return a + b

        test = Test()
        test_add = test.add(6, 9)
        self.assertIsInstance(test_add, Chainable)

        self.assertEqual((yield test_add), 15)

        return_value({})

    @test_chainable
    def test_kwargs(self):
        class Test:
            @make_deferred
            def add(self, a, b):
                return a + b

        test = Test()

        test_add = test.add(**{'a': 12, 'b': 3})
        self.assertEqual((yield test_add), 15)

        return_value({})

    @test_chainable
    def test_exception(self):
        class Test:
            @make_deferred
            def add(self):
                raise ValueError()

        test = Test()

        test_add = test.add()
        yield self.assertFailure(test_add, ValueError)

from twisted.internet.defer import Deferred
from twisted.internet.threads import deferToThread
from twisted.trial.unittest import TestCase
from twisted.internet import reactor

from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.deferred.return_value import return_value
from mdstudio.deferred.chainable import chainable

class TestMakeDeferred(TestCase):
    
    def setUp(self, *args, **kwargs):
        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

        super(TestMakeDeferred, self).setUp(*args, **kwargs)

    @chainable
    def test_no_args(self):

        class Test:

            @make_deferred
            def test(self):
                return 3

        test = Test()

        testTest = test.test()
        self.assertIsInstance(testTest, Deferred)
        self.assertEqual(3, (yield testTest))

        return_value({})

    @chainable
    def test_args(self):

        class Test:

            @make_deferred
            def add(self, a, b):
                return a + b

        test = Test()
        testAdd = test.add(6, 9)
        self.assertIsInstance(testAdd, Deferred)

        self.assertEqual((yield testAdd), 15)

        return_value({})

    @chainable
    def test_kwargs(self):

        class Test:

            @make_deferred
            def add(self, a, b):
                return a + b

        test = Test()

        testAdd = test.add(**{'a':12, 'b':3})
        self.assertEqual((yield testAdd), 15)

        return_value({})
        
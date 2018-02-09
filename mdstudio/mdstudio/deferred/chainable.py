import types
from functools import wraps

from twisted.internet import defer

from twisted.internet.defer import Deferred


# noinspection PyPep8Naming
from mdstudio.api.context import ContextManager
from mdstudio.deferred.return_value import return_value


class Chainable(object):
    @property
    def __class__(self):
        # Fake being a Deferred. We pass through everything to the deferred and catch what is not defined.
        return Deferred

    def __init__(self, deferred):
        self.__deferred = deferred

    def __call__(self, *args, **kwargs):
        # New deferred
        d = Deferred()

        def chained(result):
            # When the result of our __deferred arrives, call the function (assuming it's possible) and pass the result
            # to the new deferred
            try:
                result = result(*args, **kwargs)
                if isinstance(result, Deferred):
                    result.addCallback(d.callback)
                    result.addErrback(d.errback)
                else:
                    d.callback(result)
            except Exception as e:
                d.errback(e)

        # Register the chained function to catch the result of the old __deferred
        self.__deferred.addCallback(chained)
        self.__deferred.addErrback(d.errback)

        # Return a new wrapper to allow further chaining and yielding of results
        return Chainable(d)

    def __getitem__(self, key):
        d = Deferred()

        def unwrapped_deferred(result):
            try:
                d.callback(result[key])
            except Exception as e:
                d.errback(e)

        self.__deferred.addCallback(unwrapped_deferred)
        self.__deferred.addErrback(d.errback)

        return Chainable(d)

    def __setitem__(self, key, value):
        d = Deferred()

        def unwrapped_deferred(result):
            result[key] = value
            d.callback(None)

        self.__deferred.addCallback(unwrapped_deferred)
        self.__deferred.addErrback(d.errback)

        return Chainable(d)

    def addCallback(self, *args, **kwargs):
        return Chainable(self.__deferred.addCallback(*args, **kwargs))

    def transform(self, modifier, *args, **kwargs):
        return Chainable(self.__deferred.addCallback(modifier, *args, **kwargs))

    def addErrback(self, *args, **kwargs):
        return Chainable(self.__deferred.addErrback(*args, **kwargs))

    def addBoth(self, *args, **kwargs):
        return Chainable(self.__deferred.addBoth(*args, **kwargs))

    def addCallbacks(self, *args, **kwargs):
        return Chainable(self.__deferred.addCallbacks(*args, **kwargs))

    def __getattribute__(self, name):
        return object.__getattribute__(self, name)

    def __getattr__(self, name):
        if hasattr(self.__deferred, name):
            # If we try to address a property of the internal Deferred, pass it through
            return getattr(self.__deferred, name)
        elif name == 'result':
            # Prevent infinite nesting when the __deferred does not have a result yet
            return None
        elif name != '__deferred':
            # New deferred
            d = Deferred()

            # This will be called once the result arrives
            def unwrapped_deferred(result):
                # Get the desired attribute from the result
                res = getattr(result, name)

                if isinstance(res, Deferred):
                    # If the result is a Deferred, pass through the result once it arrives
                    res.addCallback(d.callback)
                    res.addErrback(d.errback)
                else:
                    # Otherwise, pass the attribute (possibly a function) to the new deferred for further chaining
                    d.callback(res)

            # Register the unwrapper to catch the result of the old __deferred
            self.__deferred.addCallback(unwrapped_deferred)
            self.__deferred.addErrback(d.errback)

            # Return a new wrapper to allow further chaining and yielding of results
            return Chainable(d)
        else:
            raise NotImplementedError("This execution path should not be taken")


@defer.inlineCallbacks
def inject_context(gen):
    res = None
    while True:
        try:
            res = gen.send(res)
            ctx = ContextManager.get_context()
            res = yield res
            ContextManager.set_context(ctx)
        except StopIteration:
            return_value(None)

            # Just to be sure, but break should not be reached
            break
        except defer._DefGen_Return as e:
            return_value(e.value)

            # Just to be sure, but break should not be reached
            break


def chainable(f):
    # Allow syntax like the inlineCallbacks, but instead return a Chainable with the result
    @wraps(f)
    def unwindGenerator(*args, **kwargs):
        try:
            gen = f(*args, **kwargs)
        except defer._DefGen_Return as e:
            return Chainable(defer.succeed(e.value))

        if not isinstance(gen, types.GeneratorType):
            return Chainable(defer.succeed(gen))

        return Chainable(inject_context(gen))

    return unwindGenerator


def test_chainable(f):
    # Similar to chainable, but without actually wrapping the Deferred
    @wraps(f)
    def unwindGenerator(*args, **kwargs):
        try:
            gen = f(*args, **kwargs)
        except defer._DefGen_Return as e:
            return defer.succeed(e.value)

        if not isinstance(gen, types.GeneratorType):
            return defer.succeed(gen)

        return inject_context(gen)

    return unwindGenerator

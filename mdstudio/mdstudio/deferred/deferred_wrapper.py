from twisted.internet.defer import Deferred
import time

class DeferredWrapper:
    @property
    def __class__(self):
        # Fake being a Deferred. We pass through everything to the deferred and catch what is not defined.
        return defer.Deferred

    def __init__(self, deferred):
        self.__deferred = deferred

    def __call__(self, *args, **kwargs):
        # New deferred
        d = defer.Deferred()

        def chained(result):
            # When the result of our __deferred arrives, call the function (assuming it's possible) and pass the result
            # to the new deferred
            result = result(*args, **kwargs)
            if isinstance(result, defer.Deferred):
                result.addCallback(d.callback)
            else:
                d.callback(result)
        
        # Register the chained function to catch the result of the old __deferred
        self.__deferred.addCallback(chained)

        # Return a new wrapper to allow further chaining and yielding of results
        return DeferredWrapper(d)

    def __getitem__(self, key):
        d = defer.Deferred()

        def unwrapped_deferred(result):
            d.callback(result[key])

        self.__deferred.addCallback(unwrapped_deferred)

        return DeferredWrapper(d)

    def __setitem__(self, key, value):
        d = defer.Deferred()

        def unwrapped_deferred(result):
            result[key] = value
            d.callback(None)

        self.__deferred.addCallback(unwrapped_deferred)

        return DeferredWrapper(d)

    def __getattribute__(self, name):
        return object.__getattribute__(self, name)

    def __getattr__(self, name):
        # print(name)
        if hasattr(self.__deferred, name):
            # If we try to address a property of the internal Deferred, pass it through
            return getattr(self.__deferred, name)
        elif name == 'result':
            # Prevent infinite nesting when the __deferred does not have a result yet
            return None
        elif name != '__deferred':
            # New deferred
            d = defer.Deferred()

            # This will be called once the result arrives
            def unwrapped_deferred(result):
                # Get the desired attribute from the result
                res = getattr(result, name)

                if isinstance(res, defer.Deferred):
                    # If the result is a Deferred, pass through the result once it arrives
                    res.addCallback(d.callback)
                else:
                    # Otherwise, pass the attribute (possibly a function) to the new deferred for further chaining
                    d.callback(res)

            # Register the unwrapper to catch the result of the old __deferred
            self.__deferred.addCallback(unwrapped_deferred)

            # Return a new wrapper to allow further chaining and yielding of results
            return DeferredWrapper(d)
        else:
            raise NotImplementedError("This execution path should not be taken")

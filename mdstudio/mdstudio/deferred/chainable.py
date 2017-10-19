from twisted.internet import defer

from mdstudio.deferred.deferred_wrapper import DeferredWrapper

def chainable(f):
    # Allow syntax like the inlineCallbacks, but instead return a DeferredWrapper with the result
    def _chainable(*args, **kwargs):
        deferred = defer.inlineCallbacks(f)(*args, **kwargs)
        return DeferredWrapper(deferred)

    return _chainable
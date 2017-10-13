from twisted.internet import defer

from mdstudio.deferred.deferred_wrapper import DeferredWrapper


def chainable(f):
    def _chainable(*args, **kwargs):
        d = defer.inlineCallbacks(f)(*args, **kwargs)
        return DeferredWrapper(d)

    return _chainable
from twisted.internet import defer


# noinspection PyMissingConstructor
class DeferredWrapper(defer.Deferred):
    def __init__(self, deferred):
        self.__deferred = deferred

    def __getattr__(self, name):
        if hasattr(self.__deferred, name):
            return getattr(self.__deferred, name)
        elif name != '__deferred':
            def unwrap_deferred(*args, **kwargs):
                @defer.inlineCallbacks
                def _unwrap_deferred(*args, **kwargs):
                    res = yield self.__deferred
                    result = yield getattr(res, name)(*args, **kwargs)
                    defer.returnValue(result)

                return DeferredWrapper(_unwrap_deferred(*args, **kwargs))

            return unwrap_deferred
        else:
            return self.__dict__['_DeferredWrapper{}'.format(name)]

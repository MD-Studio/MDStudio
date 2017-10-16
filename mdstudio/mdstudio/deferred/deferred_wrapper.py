from twisted.internet.defer import Deferred
import time


# noinspection PyMissingConstructor
class DeferredWrapper(Deferred):
    def __init__(self, deferred):
        self.__deferred = deferred

    def __getattr__(self, name):
        if hasattr(self.__deferred, name):
            return getattr(self.__deferred, name)
        elif name != '__deferred':
            # print(name)
            def unwrap_deferred(*args, **kwargs):
                # def _unwrap_deferred(*args, **kwargs):
                #     d = defer.Deferred()
                #     res = yield self.__deferred.addBoth()
                #     result = yield getattr(res, name)(*args, **kwargs)
                #     print(result)
                #     defer.returnValue(result)
                d = Deferred()

                def unwrapped_deferred(result):
                    res = getattr(result, name)(*args, **kwargs)
                    if isinstance(res, Deferred):
                        res.addCallback(d.callback)
                    else:
                        d.callback(res)

                self.__deferred.addCallback(unwrapped_deferred)

                return DeferredWrapper(d)

            return unwrap_deferred
        else:
            return self.__dict__['_DeferredWrapper{}'.format(name)]

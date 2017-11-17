from twisted.internet.defer import DeferredLock as _Lock

class Lock(_Lock):
    pass
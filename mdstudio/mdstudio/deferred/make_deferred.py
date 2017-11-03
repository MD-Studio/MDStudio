from typing import Callable, Any

from twisted.internet.defer import Deferred
from twisted.internet import reactor

from mdstudio.deferred.chainable import Chainable
from mdstudio.unittest import wait_for_completion

from time import sleep as blockingsleep

def make_deferred(method):
    # type: (Callable) -> Callable[Any, Chainable]
    def wrapper(instance, *args, **kwargs):
        d = Deferred()

        def _wrapper():
            try:
                d.callback(method(instance, *args, **kwargs))
            except Exception as e:
                d.errback(e)

        reactor.callInThread(_wrapper)

        if wait_for_completion.wait_for_completion and reactor.getThreadPool().started:
            while reactor.getThreadPool().working:
                blockingsleep(0.0001)

        return Chainable(d)

    return wrapper

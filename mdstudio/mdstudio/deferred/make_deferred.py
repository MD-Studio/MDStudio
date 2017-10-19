from typing import Callable, Any

from twisted.internet.defer import Deferred
from twisted.internet.threads import deferToThread

from mdstudio.deferred.chainable import Chainable


def make_deferred(method):
    # type: (Callable) -> Callable[Any, Chainable]
    def wrapper(instance, *args, **kwargs):
        return Chainable(deferToThread(method, instance, *args, **kwargs))

    return wrapper

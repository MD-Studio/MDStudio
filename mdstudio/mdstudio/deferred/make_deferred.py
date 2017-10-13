from typing import Callable, Any

from twisted.internet.defer import Deferred
from twisted.internet.threads import deferToThread


def make_deferred(method):
    # type: (Callable) -> Callable[Any, Deferred]
    def wrapper(instance, *args, **kwargs):
        return deferToThread(method, instance, *args, **kwargs)

    return wrapper

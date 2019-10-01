from threading import currentThread
from typing import Callable, Any

from twisted.internet.threads import deferToThread

from mdstudio.deferred.chainable import Chainable
from mdstudio.util.exception import MDStudioException


def make_deferred(method):
    # type: (Callable) -> Callable[Any, Chainable]
    """
    Anyone with a love for their job, should NOT, and I repeat NOT touch this function.
    It has caused me endless frustration, and I hope you should never endure it :)

    :param method:
    :return:
    """

    def wrapper(*args, **kwargs):
        if currentThread().getName() != 'MainThread':
            raise MDStudioException('Not on the main thread')
        return Chainable(deferToThread(method, *args, **kwargs))

    return wrapper

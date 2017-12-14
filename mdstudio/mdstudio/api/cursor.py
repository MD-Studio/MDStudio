# coding=utf-8
from collections import deque
from enum import Enum
from typing import *

from asq.initiators import query
from asq.queryables import Queryable
from twisted.internet.defer import succeed

from mdstudio.deferred.chainable import chainable, Chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.session import GlobalSession

query = query


class CursorRefreshingError(Exception):
    def __init__(self):
        self.message = "Yield or wait for the callback of the previous result."


class Cursor:

    class Direction(Enum):
        Forward = 1
        Backward = -1

    # type: str
    _next = None

    # type: str
    _previous = None

    # type: deque
    _data = deque()

    # type: bool
    _alive = True

    # type: int
    _returned = None

    # type: str
    _uri = None

    # type: dict
    _claims = None

    # type: dict
    _current = 0

    def __init__(self, response, claims=None, session=None):
        self._session = session or GlobalSession.session
        self._claims = claims
        self._next = response['paging'].get('next', None)
        self._previous = response['paging'].get('previous', None)
        self._alive = (self._next is not None or self._previous is not None)
        self._data = deque(response['results'])
        self._uri = response['paging']['uri']
        self._refreshing = False
        self._current = 0

    def __iter__(self):
        return self

    def next(self):
        if self._refreshing:
            raise CursorRefreshingError()

        len_data = len(self._data)
        if len_data - self._current > 1:
            result = self._data[self._current]
            self._current += 1
            return Chainable(succeed(result))
        elif self.alive and self._next:
            self._refreshing = True
            return self._refresh(self.Direction.Forward)
        elif len_data:
            result = self._data[self._current]
            self._current += 1
            return Chainable(succeed(result))
        else:
            raise StopIteration

    def previous(self):
        raise NotImplemented()

    # python 3 compatibility
    __next__ = next

    @chainable
    def for_each(self, func):
        # type: (Callable[[Dict[str,Any]], None]) -> None
        for o in self:
            o = yield o
            func(o)

    def query(self):
        # type: () -> Queryable
        return self.to_list().addCallback(lambda l: query(l))

    @chainable
    def to_list(self):
        results = []
        for doc in self:
            results.append((yield doc))

        return_value(results)

    @property
    def alive(self):
        # type: () -> bool
        return self._alive

    @staticmethod
    @chainable
    def from_uri(uri, request, claims=None, session=None):
        session = session or GlobalSession.session
        return_value(Cursor((yield session.call(uri, request, claims)), session=session, claims=claims))

    @chainable
    def _refresh(self, direction):
        if direction == self.Direction.Forward:
            more = yield self._session.call(self._uri, {
                'next': self._next
            })
            last_entry = self._data[self._current]
            self._data = more['results']
            self._current = 0
        else:
            more = yield self._session.call(self._uri, {
                'previous': self._previous
            })
            last_entry = self._data[self._current - 1]
            self._data = more['results'] + self._data[:self._current]
            self._current += len(more['results'])

        self._next = more['paging'].get('next', None)
        self._previous = more['paging'].get('previous', None)
        self._alive = (self._next is not None or self._previous is not None)
        self._refreshing = False
        return_value(last_entry)

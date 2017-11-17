# coding=utf-8
from collections import deque
from typing import *

from asq.initiators import query
from asq.queryables import Queryable
from twisted.internet.defer import succeed

from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value

query = query

class CursorRefreshingError(Exception):
    def __init__(self):
        self.message = "Yield or wait for the callback of the previous result."

class Cursor:

    # type: str
    _id = None

    # type: bool
    _alive = True

    # type: deque
    _data = deque()

    # type: int
    _returned = None

    def __init__(self, wrapper, response, date_time_fields=[]):
        self.wrapper = wrapper
        self._id = response.get('cursorId', None)
        self._alive = self._id is not None and response['alive']
        self._data = deque(response['results'])
        self._refreshing = False
        self._date_time_fields = date_time_fields

    def __iter__(self):
        return self

    def next(self):
        if self._refreshing:
            raise CursorRefreshingError()

        len_data = len(self._data)
        if len_data > 1:
            return succeed(self._data.popleft())
        elif self.alive:
            self._refreshing = True
            return self._refresh()
        elif len_data:
            return succeed(self._data.popleft())
        else:
            raise StopIteration

    # python 3 compatibility
    __next__ = next

    def __len__(self):
        return self.count(True)

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
    def rewind(self):
        # type: () -> Cursor
        self.__init__(self.wrapper, (yield self.wrapper.rewind(self._id)))

        return self

    def count(self, with_limit_and_skip=False):
        # type: (bool) -> int
        return self.wrapper.count(cursor_id=self._id, with_limit_and_skip=with_limit_and_skip)['total']

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

    @chainable
    def _refresh(self):
        more = yield self.wrapper.more(cursor_id=self._id)
        self._id = more.get('cursorId', None)
        last_entry = self._data.popleft()
        self._data = deque(more['results'])
        self._alive = self._id is not None and more['alive'] and len(self._data) > 0
        self._refreshing = False

        return_value(last_entry)

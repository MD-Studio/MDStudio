# coding=utf-8
from collections import deque
from typing import *

from asq.initiators import query
from asq.queryables import Queryable

from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


class Cursor:

    # type: str
    _id = None

    # type: bool
    _alive = True

    # type: deque
    _data = deque()

    def __init__(self, wrapper, response):
        self.wrapper = wrapper
        self.current = 0
        self._id = response['_id']
        self._alive = response['alive']
        self._data = deque(response['results'])

    def __iter__(self):
        return self

    @chainable
    def next(self):
        if len(self._data) or (yield self._refresh()):
            return_value(self._data.popleft())
        else:
            raise StopIteration

    # python 3 compatibility
    __next__ = next

    def __len__(self):
        return self.count(True)

    def for_each(self, func):
        # type: (Callable[[Dict[str,Any]], None]) -> None
        for o in self:
            func(o)

    def query(self):
        # type: () -> Queryable
        return query(self)

    @chainable
    def rewind(self):
        # type: () -> Cursor
        return_value(self._create_cursor(self.wrapper, (yield self.wrapper.rewind())))

    def count(self, with_limit_and_skip=False):
        # type: (bool) -> int
        return self.wrapper.count(cursor_id=self._id, with_limit_and_skip=with_limit_and_skip)

    @property
    def alive(self):
        # type: () -> bool
        return self._alive

    @staticmethod
    def _create_cursor(wrapper, rewind):
        return Cursor(wrapper, rewind)

    @chainable
    def _refresh(self):
        if self.alive:
            more = yield self.wrapper.more(cursor_id=self._id)
            self._id = more['_id']
            self._alive = more['alive']
            self._data = deque(more['results'])

        return_value(self._alive or len(self._data))

# coding=utf-8
from collections import deque
from typing import *

from asq.initiators import query
from asq.queryables import Queryable


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
        self._id = response['id']
        self._alive = response['alive']
        self._data = deque(response['result'])

    def __iter__(self):
        return self

    def next(self):
        if len(self._data) or self._refresh():
            return self._data.popleft()
        else:
            raise StopIteration

    # python 3 compatibility
    __next__ = next

    def for_each(self, func):
        # type: (Callable[[Dict[str,Any]], None]) -> None
        for o in self:
            func(o)

    def query(self):
        # type: () -> Queryable
        return query(self)

    def rewind(self):
        # type: () -> Cursor
        return Cursor(self.wrapper, self.wrapper.rewind())

    def count(self, with_limit_and_skip=False):
        # type: (bool) -> int
        return self.wrapper.count(cursor_id=self._id, with_limit_and_skip=with_limit_and_skip)

    @property
    def alive(self):
        # type: () -> bool
        return self.alive

    def _refresh(self):
        if self.alive:
            more = self.wrapper.more(cursor_id=self._id)
            self._alive = more['alive']
            self._data = deque(more['alive'])

        return self._alive

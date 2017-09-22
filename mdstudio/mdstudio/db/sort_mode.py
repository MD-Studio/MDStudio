# coding=utf-8

from enum import Enum


class SortMode(Enum):
    Asc = "asc"
    Desc = "desc"

    def __str__(self):
        return str(self.value)

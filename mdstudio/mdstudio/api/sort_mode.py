# coding=utf-8

from enum import Enum


class SortMode(Enum):
    Asc = 1, 'asc'
    Desc = -1, 'desc'

    def __new__(cls, value, name):
        member = object.__new__(cls)
        member._value_ = value
        member.fullname = name
        return member

    def __str__(self):
        return self.fullname

    def __int__(self):
        return self.value

    @staticmethod
    def from_string(name):
        if name == str(SortMode.Asc):
            return SortMode.Asc
        elif name == str(SortMode.Desc):
            return SortMode.Desc
        else:
            raise ValueError('Sort mode "{}" is not supported'.format(name))

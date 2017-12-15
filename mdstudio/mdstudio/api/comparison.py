# coding=utf-8

from enum import Enum


class Comparison(Enum):
    Eq = 0, 'eq'
    Gt = 1, 'gt'
    Lt = 2, 'lt'
    Gte = 3, 'gte'
    Lte = 4, 'lte'

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
        if name == str(Comparison.Eq):
            return Comparison.Eq
        elif name == str(Comparison.Gt):
            return Comparison.Gt
        elif name == str(Comparison.Lt):
            return Comparison.Lt
        elif name == str(Comparison.Gte):
            return Comparison.Gte
        elif name == str(Comparison.Lte):
            return Comparison.Lte
        else:
            raise ValueError('Sort mode "{}" is not supported'.format(name))

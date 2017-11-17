# coding=utf-8

from enum import Enum


class LogType(Enum):
    User = 0, 'user'
    Group = 1, 'group'
    GroupRole = 2, 'groupRole'

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
        if name == str(LogType.User):
            return LogType.User
        elif name == str(LogType.Group):
            return LogType.Group
        elif name == str(LogType.GroupRole):
            return LogType.GroupRole
        else:
            raise ValueError('Connection type "{}" is not supported'.format(name))

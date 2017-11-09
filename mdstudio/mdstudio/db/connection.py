# coding=utf-8

from enum import Enum


class ConnectionType(Enum):
    User = 0, "user"
    Group = 1, "group"
    GroupRole = 2, "groupRole"

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
        if name == str(ConnectionType.User):
            return ConnectionType.User
        elif name == str(ConnectionType.Group):
            return  ConnectionType.Group
        elif name == str(ConnectionType.GroupRole):
            return ConnectionType.GroupRole
        else:
            raise ValueError('Connection type "{}" is not supported'.format(name))

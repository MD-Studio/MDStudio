from typing import TypeVar

from twisted.internet.defer import returnValue


T = TypeVar('T')
def return_value(val):
    # type: (T) -> T
    returnValue(val)
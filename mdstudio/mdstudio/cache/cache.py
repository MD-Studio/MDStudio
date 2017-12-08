import abc
import six
from typing import Any, Union, List, Optional, Tuple


@six.add_metaclass(abc.ABCMeta)
class ICache(object):

    @abc.abstractmethod
    def put(self, key, value, expiry=None):
        # type: (str, Any, Optional[int]) -> dict
        raise NotImplementedError

    @abc.abstractmethod
    def put_many(self, values, expiry=None):
        # type: (List[Tuple[str, Any]], Optional[int]) -> dict
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, key):
        # type: (str) -> dict
        raise NotImplementedError

    @abc.abstractmethod
    def forget(self, keys):
        # type: (Union[List[str], str]) -> dict
        raise NotImplementedError

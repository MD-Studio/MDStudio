# coding=utf-8
from typing import *

import abc
import six

from mdstudio.db.cursor import Cursor
from mdstudio.db.fields import Fields
from mdstudio.db.index import Index
from mdstudio.db.sort_mode import SortMode
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value

try:
    from pymongo.collection import Collection

    CollectionType = Union[str, Dict[str, str], Collection]
except ImportError:
    CollectionType = Union[str, Dict[str, str]]

DocumentType = Dict
AggregationOperator = Dict
ProjectionOperators = Dict
SortOperators = Optional[Union[List[Tuple[str, SortMode]], Tuple[str, SortMode]]]
IndexKeys = Union[List[Tuple[str, SortMode]], Tuple[str, SortMode]]


# noinspection PyShadowingBuiltins
@six.add_metaclass(abc.ABCMeta)
class IDatabase(object):

    @abc.abstractmethod
    def more(self, cursor_id, claims=None):
        # type: (str, Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def rewind(self, cursor_id, claims=None):
        # type: (str, Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def insert_one(self, collection, insert, fields=None, claims=None):
        # type: (CollectionType, DocumentType, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def insert_many(self, collection, insert, fields=None, claims=None):
        # type: (CollectionType, List[DocumentType], Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def replace_one(self, collection, dbfilter, replacement, upsert=False, fields=None, claims=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def count(self, collection, dbfilter=None, skip=None, limit=None, fields=None, claims=None, cursor_id=None, with_limit_and_skip=False):
        # type: (CollectionType, Optional[DocumentType], Optional[int], Optional[int], Optional[Fields], Optional[dict], Optional[str], bool) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def update_one(self, collection, dbfilter, update, upsert=False, fields=None, claims=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def update_many(self, collection, dbfilter, update, upsert=False, fields=None, claims=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one(self, collection, dbfilter, projection=None, skip=None, sort=None, fields=None, claims=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], Optional[int], SortOperators, Optional[Fields],Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_many(self, collection, dbfilter, projection=None, skip=None, limit=None, sort=None, fields=None, claims=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], Optional[int], Optional[int], SortOperators, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_and_update(self, collection, dbfilter, update, upsert=False, projection=None, sort=None, return_updated=False, fields=None,
                            claims=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_and_replace(self, collection, dbfilter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, fields=None, claims=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_and_delete(self, collection, dbfilter, projection=None, sort=None, fields=None, claims=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], SortOperators, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def distinct(self, collection, field, dbfilter=None, fields=None, claims=None):
        # type: (CollectionType, str, Optional[DocumentType], Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def aggregate(self, collection, pipeline):
        # type: (CollectionType, List[AggregationOperator]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def delete_one(self, collection, dbfilter, fields=None, claims=None):
        # type: (CollectionType, DocumentType, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def delete_many(self, collection, dbfilter, fields=None, claims=None):
        # type: (CollectionType, DocumentType, Optional[Fields], Optional[dict]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def create_indexes(self, collection, indices):
        # type: (CollectionType, List[Index]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def drop_all_indexes(self, collection):
        # type: (CollectionType) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def drop_indexes(self, collection, indexes):
        # type: (CollectionType, List[Index]) -> Any
        raise NotImplementedError

    @chainable
    def make_cursor(self, results, fields):
        res = yield results
        return_value(Cursor(self, res, fields))

    @staticmethod
    def extract(result, prperty):
        return result[prperty]

    @staticmethod
    @chainable
    def transform(result, transformed):
        res = yield result
        return_value(None if res is None else transformed(res))

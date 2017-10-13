# coding=utf-8
from typing import *

import abc
import six

from mdstudio.db.cursor import Cursor
from mdstudio.db.sort_mode import SortMode

try:
    from pymongo.collection import Collection

    CollectionType = Union[str, Dict[str, str], Collection]
except ImportError:
    CollectionType = Union[str, Dict[str, str]]

DateFieldsType = List[Union[str, List[str]]]
DocumentType = Dict
AggregationOperator = Dict
ProjectionOperators = Dict
SortOperators = Optional[List[Tuple[str, SortMode]]]


@six.add_metaclass(abc.ABCMeta)
class IDatabase:

    @abc.abstractmethod
    def more(self, cursor_id):
        # type: (str) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def rewind(self, cursor_id):
        # type: (str) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def insert_one(self, collection, insert, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def insert_many(self, collection, insert, date_fields=None):
        # type: (CollectionType, List[DocumentType], Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def replace_one(self, collection, filter, replacement, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def count(self, collection, filter=None, skip=None, limit=None, date_fields=None, cursor_id=None, with_limit_and_skip=False):
        # type: (CollectionType, Optional[DocumentType], Optional[int], Optional[int], Optional[DateFieldsType], Optional[str], bool) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def update_one(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def update_many(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one(self, collection, filter, projection=None, skip=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], Optional[int], SortOperators, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_many(self, collection, filter, projection=None, skip=None, limit=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], Optional[int], Optional[int], SortOperators, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_and_update(self, collection, filter, update, upsert=False, projection=None, sort=None,
                            return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_and_replace(self, collection, filter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_and_delete(self, collection, filter, projection=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], SortOperators, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def distinct(self, collection, field, filter=None, date_fields=None):
        # type: (CollectionType, str, Optional[DocumentType], Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def aggregate(self, collection, pipeline):
        # type: (CollectionType, List[AggregationOperator]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def delete_one(self, collection, filter, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def delete_many(self, collection, filter, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[DateFieldsType]) -> Any
        raise NotImplementedError

    def make_cursor(self, results):
        return Cursor(self, results)

    @staticmethod
    def transform(result, transformed):
        return None if result is None else transformed(result)

    @staticmethod
    def extract(result, name):
        return result[name]

# coding=utf-8
from typing import *

import abc

from mdstudio.db.cursor import Cursor
from mdstudio.db.sort_mode import SortMode
from mdstudio.db.collection import Collection

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


class IDatabase:
    __metaclass__ = abc.ABCMeta

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
        # type: (CollectionType, DocumentType, DateFieldsType) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def insert_many(self, collection, insert, date_fields=None):
        # type: (CollectionType, List[DocumentType], DateFieldsType) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def replace_one(self, collection, filter, replacement, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def count(self, collection, filter=None, skip=None, limit=None, cursor_id=None, with_limit_and_skip=False):
        # type: (CollectionType, Optional[DocumentType], Optional[int], Optional[int], str, bool) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def update_one(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def update_many(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one(self, collection, filter, projection=None, skip=None, sort=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, Optional[int], SortOperators) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_many(self, collection, filter, projection=None, skip=None, limit=None, sort=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, Optional[int], Optional[int], SortOperators) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_and_update(self, collection, filter, update, upsert=False, projection=None, sort=None,
                            return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_and_replace(self, collection, filter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_and_delete(self, collection, filter, projection=None, sort=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, SortOperators, bool) -> Any
        raise NotImplementedError


    @abc.abstractmethod
    def distinct(self, collection, field, filter=None):
        # type: (CollectionType, str, Optional[DocumentType]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def aggregate(self, collection, pipeline):
        # type: (CollectionType, List[AggregationOperator]) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def delete_one(self, collection, filter):
        # type: (CollectionType, DocumentType) -> Any
        raise NotImplementedError

    @abc.abstractmethod
    def delete_many(self, collection, filter):
        # type: (CollectionType, DocumentType) -> Any
        raise NotImplementedError

    def make_cursor(self, results):
        return Cursor(self, results)

    @staticmethod
    def transform(result, transformed):
        return None if result is None else transformed(result)

    @staticmethod
    def extract(result, name):
        return result[name]

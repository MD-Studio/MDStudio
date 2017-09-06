from typing import *
from pymongo.collection import Collection

import abc

from mdstudio.db.sort_mode import SortMode

CollectionType = Union[str, Dict[str, str], Collection]
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
        pass

    @abc.abstractmethod
    def rewind(self, cursor_id):
        # type: (str) -> Any
        pass

    @abc.abstractmethod
    def insert_one(self, collection, insert, date_fields=None):
        # type: (CollectionType, DocumentType, DateFieldsType) -> Any
        pass

    @abc.abstractmethod
    def insert_many(self, collection, insert, date_fields=None):
        # type: (CollectionType, List[DocumentType], DateFieldsType) -> Any
        pass

    @abc.abstractmethod
    def replace_one(self, collection, filter, replacement, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Any
        pass

    @abc.abstractmethod
    def count(self, collection, filter=None, skip=0, limit=None, cursor_id=None, with_limit_and_skip=False):
        # type: (CollectionType, Optional[DocumentType], int, Optional[int], str, bool) -> Any
        pass

    @abc.abstractmethod
    def update_one(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Any
        pass

    @abc.abstractmethod
    def update_many(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Any
        pass

    @abc.abstractmethod
    def find_one(self, collection, filter, projection=None, skip=0, sort=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, int, SortOperators) -> Any
        pass

    @abc.abstractmethod
    def find_many(self, collection, filter, projection=None, skip=0, limit=None, sort=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, int, Optional[int], SortOperators) -> Any
        pass

    @abc.abstractmethod
    def find_one_and_update(self, collection, filter, update, upsert=False, projection=None, sort=None,
                            return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Any
        pass

    @abc.abstractmethod
    def find_one_and_replace(self, collection, filter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Any
        pass

    @abc.abstractmethod
    def find_one_and_delete(self, collection, filter, projection=None, sort=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, SortOperators, bool) -> Any
        pass


    @abc.abstractmethod
    def distinct(self, collection, field, filter=None):
        # type: (CollectionType, str, Optional[DocumentType]) -> Any
        pass

    @abc.abstractmethod
    def aggregate(self, collection, pipeline):
        # type: (CollectionType, List[AggregationOperator]) -> Any
        pass

    @abc.abstractmethod
    def delete_one(self, collection, filter):
        # type: (CollectionType, DocumentType) -> Any
        pass

    @abc.abstractmethod
    def delete_many(self, collection, filter):
        # type: (CollectionType, DocumentType) -> Any
        pass

    def transform(self, result, transformed):
        return None if result is None else transformed(result)

    def extract(self, result, name):
        return result[name]

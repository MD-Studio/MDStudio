# coding=utf-8
import datetime
from typing import *

import abc
import six

from mdstudio.db.cursor import Cursor
from mdstudio.db.exception import DatabaseException
from mdstudio.db.sort_mode import SortMode
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value

import pytz

from mdstudio.utc import from_utc_string

try:
    from pymongo.collection import Collection

    CollectionType = Union[str, Dict[str, str], Collection]
except ImportError:
    CollectionType = Union[str, Dict[str, str]]

DateTimeFieldsType = List[Union[str, List[str]]]
DocumentType = Dict
AggregationOperator = Dict
ProjectionOperators = Dict
SortOperators = Optional[Union[List[Tuple[str, SortMode]],Tuple[str, SortMode]]]


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

    @chainable
    def make_cursor(self, results):
        res = yield results
        return_value(Cursor(self, res))

    @staticmethod
    def extract(result, prperty):
        return result[prperty]

    @staticmethod
    @chainable
    def transform(result, transformed):
        res = yield result
        return_value(None if res is None else transformed(res))

    @staticmethod
    def transform_to_datetime(document, fields, prefixes=None):
        if fields is None:
            return

        if not isinstance(fields, list):
            fields = [fields]
        if prefixes is None:
            prefixes = ['']

        nfields = []
        for f in fields:
            if all(not f.startswith(p) for p in prefixes):
                for p in prefixes:
                    nfields.append('{}.{}'.format(p, f))
            else:
                nfields.append(f)

        for field in nfields:
            split_fields = field.split('.')
            IDatabase.transform_docfield_to_datetime(document, split_fields)

    @staticmethod
    def transform_docfield_to_datetime(doc, field):
        subdoc = doc

        for level in field[:-1]:
            if isinstance(subdoc, dict) and level in subdoc:
                subdoc = subdoc[level]
            else:
                if isinstance(subdoc, list):
                    for d in subdoc:
                        IDatabase.transform_docfield_to_datetime(d, field[1:])
                subdoc = None
                break

        if subdoc is None:
            return

        key = field[-1]

        def _parse_value(val):
            if isinstance(val, str):
                return from_utc_string(val)
            elif isinstance(val, datetime.datetime):
                if not val.tzinfo:
                    raise DatabaseException("No timezone information found. All datetime info should be stored in UTC format, please use 'mdstudio.utc.now()' and 'mdstudio.utc.to_utc_string()'")
                if val.tzinfo != pytz.utc:
                    val = val.astimezone(pytz.utc)
                return val
            else:
                raise DatabaseException("Failed to parse datetime field '{}'".format(val))

        # if we have a list of objects we support just indexing those
        if isinstance(subdoc, list):
            for d in subdoc:
                if key in d:
                    d[key] = _parse_value(d[key])
        else:
            # either we indexed a normal datetime field, or a list with datetimes
            if key in subdoc:
                if isinstance(subdoc[key], list):
                    for i, e in enumerate(subdoc[key]):
                        subdoc[key][i] = _parse_value(e)
                else:
                    subdoc[key] = _parse_value(subdoc[key])
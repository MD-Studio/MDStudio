# coding=utf-8
from typing import Optional, Union, Dict, Any, List

from autobahn.twisted import ApplicationSession
from twisted.internet.defer import Deferred

from mdstudio.db.collection import Collection
from mdstudio.db.connection import ConnectionType
from mdstudio.db.cursor import Cursor
from mdstudio.db.database import DocumentType, DateTimeFieldsType, ProjectionOperators, SortOperators, IDatabase, \
    AggregationOperator
from mdstudio.db.response import ReplaceOneResponse, UpdateOneResponse, UpdateManyResponse
from mdstudio.db.session_database import SessionDatabaseWrapper
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


class Model:

    # type: IDatabase
    wrapper = None

    # type: ConnectionType
    connection_type = ConnectionType.User

    date_time_fields = []

    # @todo: global connection
    def __init__(self, wrapper=None, collection=None, connection_type=None):
        # type: (IDatabase, Union[str, Dict[str, str], Optional[Collection]]) -> None
        if isinstance(wrapper, ApplicationSession):
            self.wrapper = SessionDatabaseWrapper(wrapper, connection_type or self.connection_type)
        else:
            self.wrapper = wrapper

        if issubclass(self.__class__, Model) and self.__class__ != Model and collection is None:
            self.collection = self.__class__.__name__.lower()
        else:
            assert collection, "No collection name was given!"
            self.collection = collection

    def insert_one(self, insert, date_time_fields=None):
        # type: (DocumentType, Optional[DateTimeFieldsType]) -> Union[str, Deferred]
        insert_one = self.wrapper.insert_one(self.collection,
                                             insert=insert,
                                             date_time_fields=self._inject_date_time_fields(date_time_fields))
        return self.wrapper.extract(insert_one, 'id')

    def insert_many(self, insert, date_time_fields=None):
        # type: (DocumentType, Optional[DateTimeFieldsType]) -> Union[List[str], Deferred]
        insert_many = self.wrapper.insert_many(self.collection,
                                               insert=insert,
                                               date_time_fields=self._inject_date_time_fields(date_time_fields))
        return self.wrapper.extract(insert_many, 'ids')

    def replace_one(self, filter, replacement, upsert=False, date_time_fields=None):
        # type: (DocumentType, DocumentType, bool, Optional[DateTimeFieldsType]) -> Dict[ReplaceOneResponse, Any]
        replace_one = self.wrapper.replace_one(self.collection,
                                               filter=filter,
                                               replacement=replacement,
                                               upsert=upsert,
                                               date_time_fields=self._inject_date_time_fields(date_time_fields))
        return self.wrapper.transform(replace_one, ReplaceOneResponse)

    def count(self, filter=None, skip=None, limit=None, date_time_fields=None, cursor_id=None, with_limit_and_skip=False):
        # type: (Optional[DocumentType], Optional[int], Optional[int], Optional[DateTimeFieldsType], Optional[str], bool) -> Union[int, Deferred]
        count = self.wrapper.count(self.collection,
                                   filter=filter,
                                   skip=skip,
                                   limit=limit,
                                   date_time_fields=self._inject_date_time_fields(date_time_fields),
                                   cursor_id=cursor_id,
                                   with_limit_and_skip=with_limit_and_skip)
        return self.wrapper.extract(count, 'total')

    def update_one(self, filter, update, upsert=False, date_time_fields=None):
        # type: (DocumentType, DocumentType, bool, Optional[DateTimeFieldsType]) -> Union[UpdateOneResponse, Deferred]
        update_one = self.wrapper.update_one(self.collection,
                                             filter=filter,
                                             update=update,
                                             upsert=upsert,
                                             date_time_fields=self._inject_date_time_fields(date_time_fields))
        return self.wrapper.transform(update_one, UpdateOneResponse)

    def update_many(self, filter, update, upsert=False, date_time_fields=None):
        # type: (DocumentType, DocumentType, bool, Optional[DateTimeFieldsType]) -> Union[UpdateManyResponse, Deferred]
        update_many = self.wrapper.update_many(self.collection,
                                               filter=filter,
                                               update=update,
                                               upsert=upsert,
                                               date_time_fields=self._inject_date_time_fields(date_time_fields))
        return self.wrapper.transform(update_many, UpdateManyResponse)

    @chainable
    def find_one(self, filter, projection=None, skip=None, sort=None, date_time_fields=None):
        # type: (DocumentType, Optional[ProjectionOperators], Optional[int], SortOperators, Optional[DateTimeFieldsType]) -> Union[Optional[dict], Deferred]
        date_time_fields = self._inject_date_time_fields(date_time_fields)
        result = self.wrapper.find_one(self.collection,
                                       filter=filter,
                                       projection=projection,
                                       skip=skip,
                                       sort=sort,
                                       date_time_fields=date_time_fields)
        result = yield self.wrapper.extract(result, 'result')
        self.wrapper.transform_to_datetime(result, date_time_fields)
        return_value(result)

    def find_many(self, filter, projection=None, skip=None, limit=None, sort=None, date_time_fields=None):
        # type: (DocumentType, Optional[ProjectionOperators], Optional[int], Optional[int], SortOperators, Optional[DateTimeFieldsType]) -> Cursor
        results = self.wrapper.find_many(self.collection,
                                         filter=filter,
                                         projection=projection,
                                         skip=skip,
                                         limit=limit,
                                         sort=sort,
                                         date_time_fields=self._inject_date_time_fields(date_time_fields))

        return self.wrapper.make_cursor(results)

    @chainable
    def find_one_and_update(self, filter, update, upsert=False, projection=None, sort=None, return_updated=False, date_time_fields=None):
        # type: (DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[DateTimeFieldsType]) -> Union[Optional[dict], Deferred]
        date_time_fields = self._inject_date_time_fields(date_time_fields)
        result = self.wrapper.find_one_and_update(self.collection,
                                                  filter=filter,
                                                  update=update,
                                                  upsert=upsert,
                                                  projection=projection,
                                                  sort=sort,
                                                  return_updated=return_updated,
                                                  date_time_fields=date_time_fields)
        result = yield self.wrapper.extract(result, 'result')
        self.wrapper.transform_to_datetime(result, date_time_fields)
        return_value(result)

    @chainable
    def find_one_and_replace(self, filter, replacement, upsert=False, projection=None, sort=None, return_updated=False, date_time_fields=None):
        # type: (DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[DateTimeFieldsType]) -> Union[Optional[dict], Deferred]
        date_time_fields = self._inject_date_time_fields(date_time_fields)
        result = self.wrapper.find_one_and_replace(self.collection,
                                                   filter=filter,
                                                   replacement=replacement,
                                                   upsert=upsert,
                                                   projection=projection,
                                                   sort=sort,
                                                   return_updated=return_updated,
                                                   date_time_fields=date_time_fields)

        result = yield self.wrapper.extract(result, 'result')
        self.wrapper.transform_to_datetime(result, date_time_fields)
        return_value(result)

    @chainable
    def find_one_and_delete(self, filter, projection=None, sort=None, date_time_fields=None):
        # type: (DocumentType, Optional[ProjectionOperators], SortOperators, Optional[DateTimeFieldsType]) -> Union[Optional[dict], Deferred]
        date_time_fields = self._inject_date_time_fields(date_time_fields)
        result = self.wrapper.find_one_and_delete(self.collection,
                                                  filter=filter,
                                                  projection=projection,
                                                  sort=sort,
                                                  date_time_fields=date_time_fields)

        result = yield self.wrapper.extract(result, 'result')
        self.wrapper.transform_to_datetime(result, date_time_fields)
        return_value(result)

    def distinct(self, field, filter=None, date_time_fields=None):
        # type: (str, Optional[DocumentType], Optional[DateTimeFieldsType]) -> Union[List[dict], Deferred]
        results = self.wrapper.distinct(self.collection,
                                        field=field,
                                        filter=filter,
                                        date_time_fields=self._inject_date_time_fields(date_time_fields))
        return self.wrapper.extract(results, 'results')

    def aggregate(self, pipeline):
        # type: (List[AggregationOperator]) -> Cursor
        results = self.wrapper.aggregate(self.collection,
                                         pipeline=pipeline)
        return self.wrapper.make_cursor(results)

    def delete_one(self, filter, date_time_fields=None):
        # type: (DocumentType, Optional[DateTimeFieldsType]) -> Union[int, Deferred]
        delete_one = self.wrapper.delete_one(self.collection,
                                             filter=filter,
                                             date_time_fields=self._inject_date_time_fields(date_time_fields))
        return self.wrapper.extract(delete_one, 'count')

    def delete_many(self, filter, date_time_fields=None):
        # type: (DocumentType, Optional[DateTimeFieldsType]) -> Union[int, Deferred]
        delete_many = self.wrapper.delete_many(self.collection,
                                               filter=filter,
                                               date_time_fields=self._inject_date_time_fields(date_time_fields))
        return self.wrapper.extract(delete_many, 'count')

    def _inject_date_time_fields(self, fields):
        if not fields:
            if not self.date_time_fields:
                return None
            fields = []
        return fields + self.date_time_fields

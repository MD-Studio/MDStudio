# coding=utf-8
from autobahn.twisted import ApplicationSession
from twisted.internet.defer import Deferred

from mdstudio.db.cursor import Cursor
from mdstudio.db.response import ReplaceOneResponse, UpdateOneResponse, UpdateManyResponse
from mdstudio.db.session_database import SessionDatabaseWrapper


class Model:

    # type: IDatabase
    wrapper = None

    def __init__(self, wrapper, collection=None):
        # type: (IDatabase, Union[str, Dict[str, str], Optional[Collection]]) -> None
        if isinstance(wrapper, ApplicationSession):
            self.wrapper = SessionDatabaseWrapper(wrapper)
        else:
            self.wrapper = wrapper

        if issubclass(self.__class__, Model) and self.__class__ != Model:
            self.collection = self.__class__.__name__.lower()
        else:
            assert collection, "No collection name was given!"
            self.collection = collection

    def insert_one(self, insert, date_fields=None):
        # type: (DocumentType, DateFieldsType) -> Union[str, Deferred]
        return self.wrapper.extract(self.wrapper.insert_one(self.collection, insert, date_fields), 'id')

    def insert_many(self, insert, date_fields=None):
        # type: (DocumentType, DateFieldsType) -> Union[List[str], Deferred]
        return self.wrapper.extract(self.wrapper.insert_many(self.collection, insert, date_fields), 'ids')

    def replace_one(self, filter, replacement, upsert=False, date_fields=None):
        # type: (DocumentType, DateFieldsType) -> Dict[ReplaceOneResponse, Any]
        replace_one = self.wrapper.replace_one(self.collection, filter, replacement, upsert, date_fields)
        return self.wrapper.transform(replace_one, ReplaceOneResponse)

    def count(self, filter=None, skip=0, limit=None, cursor_id=None, with_limit_and_skip=False):
        # type: (Optional[DocumentType], int, Optional[int], str, bool) -> Union[int, Deferred]
        count = self.wrapper.count(self.collection, filter, skip, limit, cursor_id=cursor_id,  with_limit_and_skip=with_limit_and_skip)
        return self.wrapper.extract(count, 'total')

    def update_one(self, filter, update, upsert=False, date_fields=None):
        # type: (DocumentType, DocumentType, bool, DateFieldsType) -> Union[UpdateOneResponse, Deferred]
        update_one = self.wrapper.update_one(self.collection, filter, update, upsert, date_fields)
        return self.wrapper.transform(update_one, UpdateOneResponse)

    def update_many(self, filter, update, upsert=False, date_fields=None):
        # type: (DocumentType, DocumentType, bool, DateFieldsType) -> Union[UpdateManyResponse, Deferred]
        update_many = self.wrapper.update_many(self.collection, filter, update, upsert, date_fields)
        return self.wrapper.transform(update_many, UpdateManyResponse)

    def find_one(self, filter, projection=None, skip=0, sort=None):
        # type: (DocumentType, ProjectionOperators, int, SortOperators) -> Union[Optional[dict], Deferred]
        result = self.wrapper.find_one(self.collection, filter, projection, skip, sort)
        return self.wrapper.extract(result, 'result')

    def find_many(self, filter=None, projection=None, skip=0, limit=None, sort=None):
        # type: (DocumentType, ProjectionOperators, int, Optional[int], SortOperators) -> Cursor
        results = self.wrapper.find_many(self.collection, filter, projection, skip, limit, sort)
        results = self.wrapper.extract(results, 'results')

        return self.wrapper.make_cursor(results)

    def find_one_and_update(self, filter, update, upsert=False, projection=None, sort=None,
                            return_updated=False, date_fields=None):
        # type: (DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Union[Optional[dict], Deferred]
        result = self.wrapper.find_one_and_update(self.collection, filter, update, upsert, projection, sort, return_updated, date_fields)
        return self.wrapper.extract(result, 'result')

    def find_one_and_replace(self, filter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, date_fields=None):
        # type: (DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Union[Optional[dict], Deferred]
        result = self.wrapper.find_one_and_replace(self.collection, filter, replacement, upsert, projection, sort, return_updated, date_fields)
        return self.wrapper.extract(result, 'result')

    def find_one_and_delete(self, filter, projection=None, sort=None):
        # type: (DocumentType, ProjectionOperators, SortOperators, bool) -> Union[Optional[dict], Deferred]
        result = self.wrapper.find_one_and_delete(self.collection, filter, projection, sort)
        return self.wrapper.extract(result, 'result')

    def distinct(self, field, filter=None):
        # type: (str, Optional[DocumentType]) -> Union[List[dict], Deferred]
        results = self.wrapper.distinct(self.collection, field, filter)
        return self.wrapper.extract(results, 'results')

    def aggregate(self, pipeline):
        # type: (List[AggregationOperator]) -> Cursor
        results = self.wrapper.aggregate(self.collection, pipeline)
        return self.wrapper.make_cursor(results)

    def delete_one(self, filter):
        # type: (DocumentType) -> Union[int, Deferred]
        return self.wrapper.extract(self.wrapper.delete_one(self.collection, filter), 'count')

    def delete_many(self, filter):
        # type: (DocumentType) -> Union[int, Deferred]
        return self.wrapper.extract(self.wrapper.delete_many(self.collection, filter), 'count')
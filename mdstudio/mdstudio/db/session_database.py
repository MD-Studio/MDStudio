# coding=utf-8
from typing import Dict, Any, List, Optional

from twisted.internet.defer import inlineCallbacks, returnValue

from mdstudio.db.cursor import Cursor
from mdstudio.db.database import IDatabase, CollectionType, DocumentType, DateFieldsType, ProjectionOperators, \
    SortOperators, AggregationOperator



class SessionDatabaseWrapper(IDatabase):

    def __init__(self, session):
        self.session = session
        self.namespace = session.component_info.get('namespace')

    def more(self, cursor_id):
        # type: (str) -> Dict[str, Any]

        return self.session.call(u'mdstudio.db.endpoint.more.{}'.format(self.namespace), {
            'cursorId': cursor_id
        })

    def rewind(self, cursor_id):
        # type: (str) -> Dict[str, Any]

        return self.session.call(u'mdstudio.db.endpoint.rewind.{}'.format(self.namespace), {
            'cursorId': cursor_id
        })

    def insert_one(self, collection, insert, date_fields=None):
        # type: (CollectionType, DocumentType, DateFieldsType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'insert': insert
        }
        if date_fields:
            request['fields'] = {
                'date': date_fields
            }

        return self.session.call(u'mdstudio.db.endpoint.insert_one.{}'.format(self.namespace), request)

    def insert_many(self, collection, insert, date_fields=None):
        # type: (CollectionType, List[DocumentType], DateFieldsType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'insert': insert
        }
        if date_fields:
            request['fields'] = {
                'date': date_fields
            }

        return self.session.call(u'mdstudio.db.endpoint.insert_many.{}'.format(self.namespace), request)

    def replace_one(self, collection, filter, replacement, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter,
            'replacement': replacement,
            'upsert': upsert
        }
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.endpoint.replace_one.{}'.format(self.namespace), request)

    def count(self, collection, filter=None, skip=None, limit=None, cursor_id=None, with_limit_and_skip=False):
        # type: (CollectionType, Optional[DocumentType], Optional[int], Optional[int], str, bool) -> Dict[str, Any]
        request = {
            'collection': collection
        }
        # either we use the cursor_id or we start a new query
        if cursor_id:
            request['cursorId'] = cursor_id
            if with_limit_and_skip:
                request['withLimitAndSkip'] = with_limit_and_skip
        else:
            if filter:
                request['filter'] = filter
            if skip:
                request['skip'] = skip
            if limit:
                request['limit'] = limit

        return self.session.call(u'mdstudio.db.endpoint.count.{}'.format(self.namespace), request)

    def update_one(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter,
            'update': update
        }
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.endpoint.update_one.{}'.format(self.namespace), request)

    def update_many(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter,
            'update': update
        }
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.endpoint.update_many.{}'.format(self.namespace), request)

    def find_one(self, collection, filter, projection=None, skip=None, sort=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, Optional[int], SortOperators, DateFieldsType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter
        }

        if projection:
            request['projection'] = projection
        if skip:
            request['skip'] = skip
        if sort:
            request['sort'] = sort

        return self.session.call(u'mdstudio.db.endpoint.find_one.{}'.format(self.namespace), request)

    def find_many(self, collection, filter, projection=None, skip=None, limit=None, sort=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, Optional[int], Optional[int], SortOperators) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter
        }

        if projection:
            request['projection'] = projection
        if skip:
            request['skip'] = skip
        if limit:
            request['limit'] = limit
        if sort:
            request['sort'] = sort

        return self.session.call(u'mdstudio.db.endpoint.find_many.{}'.format(self.namespace), request)

    def find_one_and_update(self, collection, filter, update, upsert=False, projection=None, sort=None,
                            return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter,
            'update': update,
            'upsert': upsert,
            'returnUpdated': return_updated
        }

        if projection:
            request['projection'] = projection
        if sort:
            request['sort'] = sort
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.endpoint.find_one_and_update.{}'.format(self.namespace), request)

    def find_one_and_replace(self, collection, filter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter,
            'replacement': replacement,
            'upsert': upsert,
            'returnUpdated': return_updated
        }

        if projection:
            request['projection'] = projection
        if sort:
            request['sort'] = sort
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.endpoint.find_one_and_replace.{}'.format(self.namespace), request)

    def find_one_and_delete(self, collection, filter, projection=None, sort=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, SortOperators, bool) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter
        }

        if projection:
            request['projection'] = projection
        if sort:
            request['sort'] = sort

        return self.session.call(u'mdstudio.db.endpoint.find_one_and_delete.{}'.format(self.namespace), request)

    def distinct(self, collection, field, query=None):
        # type: (CollectionType, str, Optional[DocumentType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'field': field
        }

        if query:
            request['query'] = query

        return self.session.call(u'mdstudio.db.endpoint.distinct.{}'.format(self.namespace), request)

    def aggregate(self, collection, pipeline):
        # type: (CollectionType, List[AggregationOperator]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'pipeline': pipeline
        }

        return self.session.call(u'mdstudio.db.endpoint.aggregate.{}'.format(self.namespace), request)

    def delete_one(self, collection, filter):
        # type: (CollectionType, DocumentType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter
        }

        return self.session.call(u'mdstudio.db.endpoint.delete_one.{}'.format(self.namespace), request)

    def delete_many(self, collection, filter):
        # type: (CollectionType, DocumentType) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter
        }

        return self.session.call(u'mdstudio.db.endpoint.delete_many.{}'.format(self.namespace), request)

    @staticmethod
    @inlineCallbacks
    def extract(result, property):
        res = yield result
        returnValue(res[property])

    @staticmethod
    @inlineCallbacks
    def transform(result, transformed):
        res = yield result
        returnValue(None if res is None else transformed(res))

    @inlineCallbacks
    def make_cursor(self, results):
        res = yield results
        returnValue(Cursor(self, res))
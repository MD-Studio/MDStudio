# coding=utf-8
import copy
from typing import Dict, Any, List, Optional

import six

from mdstudio.api.context import ContextCallable
from mdstudio.db.sort_mode import SortMode
from mdstudio.db.connection_type import ConnectionType
from mdstudio.db.cursor import Cursor
from mdstudio.db.database import IDatabase, CollectionType, DocumentType, Fields, ProjectionOperators, \
    SortOperators, AggregationOperator
from mdstudio.db.index import Index
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


# noinspection PyShadowingBuiltins
class SessionDatabaseWrapper(IDatabase, ContextCallable):

    def __init__(self, session, connection_type=ConnectionType.User):
        # type: (CommonSession, ConnectionType) -> None
        self.session = session  # type: CommonSession

        self.connection_type = connection_type
        ContextCallable.__init__(self, session)

    def more(self, cursor_id):
        # type: (str) -> Dict[str, Any]

        return self._call('more', {
            'cursorId': cursor_id
        })

    def rewind(self, cursor_id):
        # type: (str) -> Dict[str, Any]

        return self._call('rewind', {
            'cursorId': cursor_id
        })

    def insert_one(self, collection, insert, fields=None):
        # type: (CollectionType, DocumentType, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'insert': insert
        }
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('insert_one', request)

    def insert_many(self, collection, insert, fields=None):
        # type: (CollectionType, List[DocumentType], Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'insert': insert
        }
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('insert_many', request)

    def replace_one(self, collection, dbfilter, replacement, upsert=False, fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter,
            'replacement': replacement,
            'upsert': upsert
        }
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('replace_one', request)

    def count(self, collection, dbfilter=None, skip=None, limit=None, fields=None, cursor_id=None, with_limit_and_skip=False):
        # type: (CollectionType, Optional[DocumentType], Optional[int], Optional[int], Optional[Fields], Optional[str], bool) -> Dict[str, Any]
        request = {
            'collection': collection
        }
        # either we use the cursor_id or we start a new query
        if cursor_id:
            request['cursorId'] = cursor_id
            if with_limit_and_skip:
                request['withLimitAndSkip'] = with_limit_and_skip
        else:
            if dbfilter:
                request['dbfilter'] = dbfilter
            if skip:
                request['skip'] = skip
            if limit:
                request['limit'] = limit
            if fields:
                request['fields'] = fields.to_dict()

        return self._call('count', request)

    def update_one(self, collection, dbfilter, update, upsert=False, fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter,
            'update': update
        }
        if upsert:
            request['upsert'] = upsert
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('update_one', request)

    def update_many(self, collection, dbfilter, update, upsert=False, fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter,
            'update': update
        }
        if upsert:
            request['upsert'] = upsert
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('update_many', request)

    def find_one(self, collection, dbfilter, projection=None, skip=None, sort=None, fields=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], Optional[int], SortOperators, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter
        }

        if projection:
            request['projection'] = projection
        if skip:
            request['skip'] = skip
        if sort:
            request['sort'] = self._prepare_sortmode(sort)
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('find_one', request)

    def find_many(self, collection, dbfilter, projection=None, skip=None, limit=None, sort=None, fields=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], Optional[int], Optional[int], SortOperators, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter
        }

        if projection:
            request['projection'] = projection
        if skip:
            request['skip'] = skip
        if limit:
            request['limit'] = limit
        if sort:
            request['sort'] = self._prepare_sortmode(sort)
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('find_many', request)

    def find_one_and_update(self, collection, dbfilter, update, upsert=False, projection=None, sort=None,
                            return_updated=False, fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter,
            'update': update,
            'upsert': upsert,
            'returnUpdated': return_updated
        }

        if projection:
            request['projection'] = projection
        if sort:
            request['sort'] = self._prepare_sortmode(sort)
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('find_one_and_update', request)

    def find_one_and_replace(self, collection, dbfilter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter,
            'replacement': replacement,
            'upsert': upsert,
            'returnUpdated': return_updated
        }

        if projection:
            request['projection'] = projection
        if sort:
            request['sort'] = self._prepare_sortmode(sort)
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('find_one_and_replace', request)

    def find_one_and_delete(self, collection, dbfilter, projection=None, sort=None, fields=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], SortOperators, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter
        }

        if projection:
            request['projection'] = projection
        if sort:
            request['sort'] = self._prepare_sortmode(sort)
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('find_one_and_delete', request)

    def distinct(self, collection, field, query=None, fields=None):
        # type: (CollectionType, str, Optional[DocumentType], Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'field': field
        }

        if query:
            request['query'] = query
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('distinct', request)

    def aggregate(self, collection, pipeline):
        # type: (CollectionType, List[AggregationOperator]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'pipeline': pipeline
        }

        return self._call('aggregate', request)

    def delete_one(self, collection, dbfilter, fields=None):
        # type: (CollectionType, DocumentType, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter
        }
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('delete_one', request)

    def delete_many(self, collection, dbfilter, fields=None):
        # type: (CollectionType, DocumentType, Optional[Fields]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'dbfilter': dbfilter
        }
        if fields:
            request['fields'] = fields.to_dict()

        return self._call('delete_many', request)

    def create_indexes(self, collection, indexes):
        # type: (CollectionType, str, List[Index]) -> Any
        indexes = []

        for i in indexes:
            indexes.append(i.to_dict(create=True, to_mongo=False))

        return self._call('create_indexes', {
            'collection': collection,
            'indexes': indexes
        })

    def drop_indexes(self, collection, indexes):
        # type: (CollectionType, str, List[Index]) -> Any
        db_collection = self._get_collection(collection)
        indexes = []

        for i in indexes:
            indexes.append(i.to_dict(create=False, name_exclusive=True, to_mongo=False))

        return self._call('drop_indexes', {
            'collection': collection,
            'indexes': indexes
        })

    def drop_all_indexes(self, collection):
        # type: (CollectionType, str) -> Any
        db_collection = self._get_collection(collection)

        if db_collection:
            db_collection.drop_indexes()

    @chainable
    def make_cursor(self, results, fields):
        res = yield results
        return_value(Cursor(self, res, fields))

    def _prepare_sortmode(self, sort):

        if not sort:
            return sort

        sort = copy.deepcopy(sort)
        if isinstance(sort, list):
            for i, (name, mode) in enumerate(sort):
                sort[i] = [name, str(mode)]
        else:
            sort = [[sort[0], str(sort[1])]]
        return sort


    def _call(self, uri, request):
        return self.session.call('mdstudio.db.endpoint.{}'.format(uri), request,
                                 claims=self.call_context.get_db_claims(self.connection_type))

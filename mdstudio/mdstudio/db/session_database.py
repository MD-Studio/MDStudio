# coding=utf-8
from typing import Dict, Any, List, Optional

from twisted.internet.defer import inlineCallbacks, returnValue

from mdstudio.application_session import BaseApplicationSession
from mdstudio.db.connection import ConnectionType
from mdstudio.db.cursor import Cursor
from mdstudio.db.database import IDatabase, CollectionType, DocumentType, DateFieldsType, ProjectionOperators, \
    SortOperators, AggregationOperator
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


class SessionDatabaseWrapper(IDatabase):

    def __init__(self, session, connection_type):
        # type: (BaseApplicationSession, ConnectionType) -> None
        self.session = session

        self.auth_meta = {
            'connectionType': str(connection_type),
        }

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

    def insert_one(self, collection, insert, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[DateFieldsType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'insert': insert
        }
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('insert_one', request)

    def insert_many(self, collection, insert, date_fields=None):
        # type: (CollectionType, List[DocumentType], Optional[DateFieldsType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'insert': insert
        }
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('insert_many', request)

    def replace_one(self, collection, filter, replacement, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[DateFieldsType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter,
            'replacement': replacement,
            'upsert': upsert
        }
        if date_fields:
            request['fields'] = {'datetime': date_fields}

        return self._call('replace_one', request)

    def count(self, collection, filter=None, skip=None, limit=None, date_fields=None, cursor_id=None, with_limit_and_skip=False):
        # type: (CollectionType, Optional[DocumentType], Optional[int], Optional[int], Optional[DateFieldsType], Optional[str], bool) -> Dict[str, Any]
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
            if date_fields:
                request['fields'] = {
                    'datetime': date_fields
                }

        return self._call('count', request)

    def update_one(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[DateFieldsType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter,
            'update': update
        }
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('update_one', request)

    def update_many(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[DateFieldsType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter,
            'update': update
        }
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('update_many', request)

    def find_one(self, collection, filter, projection=None, skip=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], Optional[int], SortOperators, Optional[DateFieldsType]) -> Dict[str, Any]
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
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('find_one', request)

    def find_many(self, collection, filter, projection=None, skip=None, limit=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], Optional[int], Optional[int], SortOperators, Optional[DateFieldsType]) -> Dict[str, Any]
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
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('find_many', request)

    def find_one_and_update(self, collection, filter, update, upsert=False, projection=None, sort=None,
                            return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[DateFieldsType]) -> Dict[str, Any]
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
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('find_one_and_update', request)

    def find_one_and_replace(self, collection, filter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[ProjectionOperators], SortOperators, bool, Optional[DateFieldsType]) -> Dict[str, Any]
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
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('find_one_and_replace', request)

    def find_one_and_delete(self, collection, filter, projection=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[ProjectionOperators], SortOperators, Optional[DateFieldsType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter
        }

        if projection:
            request['projection'] = projection
        if sort:
            request['sort'] = sort
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('find_one_and_delete', request)

    def distinct(self, collection, field, query=None, date_fields=None):
        # type: (CollectionType, str, Optional[DocumentType], Optional[DateFieldsType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'field': field
        }

        if query:
            request['query'] = query
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('distinct', request)

    def aggregate(self, collection, pipeline):
        # type: (CollectionType, List[AggregationOperator]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'pipeline': pipeline
        }

        return self._call('aggregate', request)

    def delete_one(self, collection, filter, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[DateFieldsType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter
        }
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('delete_one', request)

    def delete_many(self, collection, filter, date_fields=None):
        # type: (CollectionType, DocumentType, Optional[DateFieldsType]) -> Dict[str, Any]
        request = {
            'collection': collection,
            'filter': filter
        }
        if date_fields:
            request['fields'] = {
                'datetime': date_fields
            }

        return self._call('delete_many', request)

    @chainable
    def make_cursor(self, results):
        res = yield results
        return_value(Cursor(self, res))

    def _call(self, uri, request):
        return self.session.call('mdstudio.db.endpoint.{}'.format(uri), request, auth_meta=self.auth_meta)
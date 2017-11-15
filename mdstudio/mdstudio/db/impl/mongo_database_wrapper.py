# -*- coding: utf-8 -*-
import datetime
from typing import Optional, Dict, Any, List

import copy
import hashlib
import pytz
import random
from bson import ObjectId
from dateutil.parser import parse as parsedate
from pymongo import ReturnDocument
from pymongo.cursor import Cursor

from mdstudio.db.cache_dict import CacheDict
from mdstudio.db.exception import DatabaseException
from mdstudio.db.database import IDatabase, CollectionType, DocumentType, DateFieldsType, SortOperators, \
    ProjectionOperators, AggregationOperator
from mdstudio.db.sort_mode import SortMode
from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.utc import to_utc_string


class MongoDatabaseWrapper(IDatabase):
    _database_name = None
    _db = None

    # type: CacheDict
    _cursors = None

    def __init__(self, database_name, db):
        self._database_name = database_name
        self._db = db

        # store the cursors for 10 minutes as described here
        # https://docs.mongodb.com/v3.0/core/cursors/
        # @TODO:  this method is really insecure since we can ask arbitrary cursors,
        #         and should be fixed ASAP
        self._cursors = CacheDict(max_age_seconds=10 * 60)

    @make_deferred
    def more(self, cursor_id):
        # type: (str) -> Dict[str, Any]
        return self._more(cursor_id)

    @make_deferred
    def rewind(self, cursor_id):
        # type: (str) -> Dict[str, Any]
        try:
            self._cursors[cursor_id].rewind()

            return self._more(cursor_id)
        except KeyError:
            raise DatabaseException("Cursor with id '{}' is unknown".format(cursor_id))

    @make_deferred
    def insert_one(self, collection, insert, date_fields=None):
        # type: (CollectionType, DocumentType, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, True)

        insert = self._prepare_for_mongo(insert)
        self.transform_to_datetime({'insert': insert}, date_fields, ['insert'])

        return {
            'id': str(db_collection.insert_one(insert).inserted_id)
        }

    @make_deferred
    def insert_many(self, collection, insert, date_fields=None):
        # type: (CollectionType, List[DocumentType], DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, True)

        insert = self._prepare_for_mongo(insert)

        self.transform_to_datetime({'insert': insert}, date_fields, ['insert'])

        return {
            'ids': [str(oid) for oid in db_collection.insert_many(insert).inserted_ids]
        }

    @make_deferred
    def replace_one(self, collection, filter, replacement, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, upsert)

        if not db_collection:
            return self._update_response(upsert)

        filter = self._prepare_for_mongo(filter)
        replacement = self._prepare_for_mongo(replacement)
        self.transform_to_datetime({'filter': filter, 'replacement': replacement}, date_fields,
                                    ['filter', 'replacement'])

        replace_result = db_collection.replace_one(filter, replacement, upsert)

        return self._update_response(upsert, result=replace_result)

    @make_deferred
    def count(self, collection=None, filter=None, skip=None, limit=None, date_fields=None, cursor_id=None,
              with_limit_and_skip=False):
        # type: (CollectionType, Optional[DocumentType], Optional[int], Optional[int], Optional[DateFieldsType], Optional[str]) -> Dict[str, Any]
        total = 0
        if cursor_id:
            total = self._cursors[cursor_id].count(with_limit_and_skip)
        else:
            db_collection = self._get_collection(collection)

            skip = 0 if not skip else skip
            limit = 0 if not limit else limit

            if db_collection:
                filter = self._prepare_for_mongo(filter)
                self.transform_to_datetime({'filter': filter}, date_fields, ['filter'])

                total = db_collection.count(filter, skip=skip, limit=limit)

        return {
            'total': total
        }

    @make_deferred
    def update_one(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, Optional[DateFieldsType]) -> Dict[str, Any]
        db_collection = self._get_collection(collection, upsert)

        if not db_collection:
            return self._update_response(upsert)

        filter = self._prepare_for_mongo(filter)
        update = self._prepare_for_mongo(update)
        self.transform_to_datetime({'filter': filter, 'update': update}, date_fields, ['filter', 'update'])

        result = db_collection.update_one(filter, update, upsert)

        return self._update_response(upsert, result=result)

    @make_deferred
    def update_many(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, upsert)

        if not db_collection:
            return self._update_response(upsert)

        filter = self._prepare_for_mongo(filter)
        update = self._prepare_for_mongo(update)
        self.transform_to_datetime({'filter': filter, 'update': update}, date_fields, ['filter', 'update'])

        result = db_collection.update_many(filter, update, upsert)

        return self._update_response(upsert, result=result)

    @make_deferred
    def find_one(self, collection, filter, projection=None, skip=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, Optional[int], SortOperators, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        skip = 0 if not skip else skip

        result = None
        if db_collection:
            filter = self._prepare_for_mongo(filter)
            self.transform_to_datetime({'filter': filter}, date_fields, ['filter'])
            result = db_collection.find_one(filter, projection, skip=skip, sort=self._prepare_sortmode(sort))

            self._prepare_for_json(result)

        return {
            'result': result
        }

    @make_deferred
    def find_many(self, collection, filter, projection=None, skip=None, limit=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, Optional[int], Optional[int], SortOperators, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        skip = 0 if not skip else skip
        limit = 0 if not limit else limit

        if not db_collection:
            return {
                'results': [],
                'alive': False,
                'size': 0
            }

        filter = self._prepare_for_mongo(filter)
        self.transform_to_datetime({'filter': filter}, date_fields, ['filter'])

        cursor = db_collection.find(filter, projection, skip=skip, limit=limit, sort=self._prepare_sortmode(sort))

        return self._get_cursor(cursor)

    @make_deferred
    def find_one_and_update(self, collection, filter, update, upsert=False, projection=None, sort=None,
                            return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, upsert)

        result = None
        if db_collection:
            filter = self._prepare_for_mongo(filter)
            update = self._prepare_for_mongo(update)
            self.transform_to_datetime({'filter': filter, 'update': update}, date_fields, ['filter', 'update'])

            return_document = ReturnDocument.BEFORE if not return_updated else ReturnDocument.AFTER
            result = db_collection.find_one_and_update(filter, update, projection, sort=self._prepare_sortmode(sort),
                                                       upsert=upsert, return_document=return_document)
            self._prepare_for_json(result)

        return {
            'result': result
        }

    @make_deferred
    def find_one_and_replace(self, collection, filter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, upsert)

        result = None
        if db_collection:
            filter = self._prepare_for_mongo(filter)
            replacement = self._prepare_for_mongo(replacement)
            self.transform_to_datetime({'filter': filter, 'replacement': replacement}, date_fields,
                                        ['filter', 'replacement'])

            return_document = ReturnDocument.BEFORE if not return_updated else ReturnDocument.AFTER
            result = db_collection.find_one_and_replace(filter, replacement, projection,
                                                        sort=self._prepare_sortmode(sort), upsert=upsert,
                                                        return_document=return_document)
            self._prepare_for_json(result)

        return {
            'result': result
        }

    @make_deferred
    def find_one_and_delete(self, collection, filter, projection=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, SortOperators, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        result = None
        if db_collection:
            filter = self._prepare_for_mongo(filter)
            self.transform_to_datetime({'filter': filter}, date_fields, ['filter'])
            result = db_collection.find_one_and_delete(filter, projection, sort=self._prepare_sortmode(sort))
            self._prepare_for_json(result)

        return {
            'result': result
        }

    @make_deferred
    def distinct(self, collection, field, filter=None, date_fields=None):
        # type: (CollectionType, str, Optional[DocumentType], DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        results = []
        if db_collection:
            filter = self._prepare_for_mongo(filter)
            self.transform_to_datetime({'filter': filter}, date_fields, ['filter'])
            results = db_collection.distinct(field, filter)
            for result in results:
                self._prepare_for_json(result)

        return {
            'results': results,
            'total': len(results)
        }

    @make_deferred
    def aggregate(self, collection, pipeline):
        # type: (CollectionType, List[AggregationOperator]) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        if not db_collection:
            return {
                'results': [],
                'alive': False,
                'size': 0
            }

        cursor = db_collection.aggregate(pipeline)

        return self._get_cursor(cursor)

    @make_deferred
    def delete_one(self, collection, filter, date_fields=None):
        # type: (CollectionType, DocumentType, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        count = 0
        if db_collection:
            filter = self._prepare_for_mongo(filter)
            self.transform_to_datetime({'filter': filter}, date_fields, ['filter'])
            count = db_collection.delete_one(filter).deleted_count
        return {
            'count': count
        }

    @make_deferred
    def delete_many(self, collection=None, filter=None, date_fields=None):
        # type: (CollectionType, DocumentType, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        count = 0
        if db_collection:
            filter = self._prepare_for_mongo(filter)
            self.transform_to_datetime({'filter': filter}, date_fields, ['filter'])
            count = db_collection.delete_many(filter).deleted_count
        return {
            'count': count
        }

    def _prepare_for_json(self, doc):
        if doc:
            # convert _id from ObjectId to str representation
            if isinstance(doc, dict) and '_id' in doc:
                doc['_id'] = str(doc['_id'])

            # convert all datetime fields to str representation
            self._transform_datetime_to_isostring(doc)

    def _prepare_for_mongo(self, doc):
        def _prepare_obj(obj):
            if obj:
                # convert json _id from str to ObjectId
                if '_id' in obj:
                    obj['_id'] = ObjectId(obj['_id'])

        doc = copy.deepcopy(doc)
        if isinstance(doc, list):

            for d in doc:
                _prepare_obj(d)
        else:
            _prepare_obj(doc)

        return doc

    def _prepare_sortmode(self, sort):
        if not sort:
            return sort

        def _convert_mode(mode):
            if isinstance(mode, str):
                mode = SortMode.Desc if mode == "desc" else SortMode.Asc
            return int(mode)

        sort = copy.deepcopy(sort)
        if isinstance(sort, list):
            for i, (name, mode) in enumerate(sort):
                sort[i] = (name, _convert_mode(mode))
        else:
            sort = [(sort[0], _convert_mode(sort[1]))]
        return sort

    def _get_cursor(self, cursor, max_size=50):
        # type: (Cursor) -> dict

        results = []

        # We have to deal with mock cursors and command cursors
        try:
            size = cursor._refresh()

            for _ in range(size):
                doc = cursor.next()
                self._prepare_for_json(doc)
                results.append(doc)
        except AttributeError:
            for doc in cursor:
                self._prepare_for_json(doc)
                results.append(doc)
                if len(results) >= max_size:
                    break
            size = len(results)

        # cache the cursor for later use
        # by default it will be available for 10 minutes we also
        # hash the cursor id to make random guessing a lot harder
        id = getattr(cursor, '_id', getattr(cursor, 'cursor_id', random.randint(1, 999999999)))
        cursor_hash = hashlib.sha256('{}{}'.format(id, random.randint(1, 999999999)).encode()).hexdigest()
        self._cursors[cursor_hash] = cursor

        return {
            'results': results,
            'size': size,
            'cursorId': cursor_hash,
            'alive': getattr(cursor, 'alive', True) and len(results) > 0
        }

    def _more(self, cursor_id):
        # type: (str) -> Dict[str, Any]

        try:
            cursor = self._cursors[cursor_id]

            # refresh cursor keep alive time
            self._cursors[cursor_id] = cursor

            return self._get_cursor(cursor)

        except KeyError:
            raise DatabaseException("Cursor with id '{}' is unknown".format(cursor_id))

    def _update_response(self, upsert, result=None):
        if result is None:
            return {
                'matched': 0,
                'modified': 0
            }

        response = {
            'matched': result.matched_count,
            'modified': result.modified_count
        }

        if upsert and result.upserted_id:
            response['upsertedId'] = str(result.upserted_id)

        return response

    def _get_collection(self, collection=None, create=False):
        if isinstance(collection, dict):
            collection_name = collection['name']
        else:
            collection_name = collection

        if collection_name not in self._db.collection_names():
            if create:
                # @todo
                # logger.info('Creating collection {collection} in {database}', collection=collection_name,
                #            database=self._database_name)
                pass
            else:
                return None

        return self._db[collection_name]

    def _transform_datetime_to_isostring(self, document):
        if isinstance(document, dict):
            iter = document.items()
        elif isinstance(document, list):
            iter = enumerate(document)
        else:
            return

        for key, value in iter:
            if isinstance(value, datetime.datetime):
                document[key] = to_utc_string(value.astimezone(pytz.utc))
            else:
                self._transform_datetime_to_isostring(value)

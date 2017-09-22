# -*- coding: utf-8 -*-

import datetime

import hashlib
import pytz
import random
from dateutil.parser import parse as parsedate
from mdstudio.db.database import IDatabase
from pymongo import MongoClient, ReturnDocument
from bson import ObjectId
from twisted.logger import Logger

from .cache_dict import CacheDict

logger = Logger(namespace='db')


class MongoDatabaseWrapper(IDatabase):
    _namespace = None
    _db = None

    # type: CacheDict
    _cursors = None

    def __init__(self, namespace, db):
        self._namespace = namespace
        self._db = db

        # store the cursors for 10 minutes as described here
        # https://docs.mongodb.com/v3.0/core/cursors/
        # @TODO:  this method is really insecure since we can ask arbitrary cursors,
        #         and should be fixed ASAP
        self._cursors = CacheDict(max_age_seconds=10 * 60)

    def more(self, cursor_id):
        # type: (str) -> Dict[str, Any]
        cursor = self._cursors[cursor_id].next()

        # refresh cursor keep alive time
        self._cursors[cursor_id] = cursor

        return self._get_cursor(cursor)

    def rewind(self, cursor_id):
        # type: (str) -> Dict[str, Any]
        self._cursors[cursor_id].rewind()

        return self.more(cursor_id)

    def insert_one(self, collection, insert, date_fields=None):
        # type: (CollectionType, DocumentType, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, True)

        self._prepare_for_mongo(insert)
        self._transform_to_datetime({'insert': insert}, date_fields)

        return {
            'id': str(db_collection.insert_one(insert).inserted_id)
        }

    def insert_many(self, collection, insert, date_fields=None):
        # type: (CollectionType, List[DocumentType], DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, True)

        for doc in insert:
            self._prepare_for_mongo(doc)

        self._transform_to_datetime({'insert': insert}, date_fields)

        return {
            'ids': [str(oid) for oid in db_collection.insert_many(insert).inserted_ids]
        }

    def replace_one(self, collection, filter, replacement, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, upsert)

        if not db_collection:
            return self._update_response(upsert)

        self._prepare_for_mongo(filter)
        self._prepare_for_mongo(replacement)
        self._transform_to_datetime({'filter': filter, 'replacement': replacement}, date_fields)

        replace_result = db_collection.replace_one(filter, replacement, upsert)

        return self._update_response(upsert, replace_result=replace_result)

    def count(self, collection=None, filter=None, skip=0, limit=0, date_fields=None, cursor_id=None,
              with_limit_and_skip=False):
        # type: (CollectionType, Optional[DocumentType], int, DateFieldsType, str, bool) -> Dict[str, Any]
        total = 0
        if cursor_id:
            total = self._cursors[cursor_id].count(with_limit_and_skip)
        else:
            db_collection = self._get_collection(collection)

            if db_collection:
                self._prepare_for_mongo(filter)
                self._transform_to_datetime({'filter': filter}, date_fields)

                total = db_collection.count(filter, skip=skip, limit=limit)

        return {
            'total': total
        }

    def update_one(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, upsert)

        if not db_collection:
            return self._update_response(upsert)

        self._prepare_for_mongo(filter)
        self._prepare_for_mongo(update)
        self._transform_to_datetime({'filter': filter, 'update': update}, date_fields)

        replace_result = db_collection.update_one(filter, update, upsert)

        return self._update_response(upsert, replace_result=replace_result)

    def update_many(self, collection, filter, update, upsert=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection, upsert)

        if not db_collection:
            return self._update_response(upsert)

        self._prepare_for_mongo(filter)
        self._prepare_for_mongo(update)
        self._transform_to_datetime({'filter': filter, 'update': update}, date_fields)

        replace_result = db_collection.update_many(filter, update, upsert)

        return self._update_response(upsert, replace_result=replace_result)

    def find_one(self, collection, filter, projection=None, skip=0, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, int, SortOperators, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        result = None
        if db_collection:
            self._prepare_for_mongo(filter)
            self._transform_to_datetime({'filter': filter}, date_fields)
            result = db_collection.find_one(filter, projection, skip, sort=sort)

            self._prepare_for_json(result)

        return {
            'result': result
        }

    def find_many(self, collection, filter, projection=None, skip=0, limit=0, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, int, Optional[int], SortOperators, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        if not db_collection:
            return {
                'results': [],
                'alive': False,
                'size': 0
            }

        self._prepare_for_mongo(filter)
        self._transform_to_datetime({'filter': filter}, date_fields)

        cursor = db_collection.find(filter, projection, skip, sort=sort)

        return self._get_cursor(cursor)

    def find_one_and_update(self, collection, filter, update, upsert=False, projection=None, sort=None,
                            return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        result = None
        if db_collection:
            self._prepare_for_mongo(filter)
            self._prepare_for_mongo(update)
            self._transform_to_datetime({'filter': filter, 'update': update}, date_fields)

            result = db_collection.find_one_and_update(filter, update, projection, sort=sort, upsert=upsert,
                                                       return_document=ReturnDocument.BEFORE if not return_updated else ReturnDocument.AFTER)
            self._prepare_for_json(result)

        return {
            'result': result
        }

    def find_one_and_replace(self, collection, filter, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, date_fields=None):
        # type: (CollectionType, DocumentType, DocumentType, bool, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        result = None
        if db_collection:
            self._prepare_for_mongo(filter)
            self._prepare_for_mongo(replacement)
            self._transform_to_datetime({'filter': filter, 'replacement': replacement}, date_fields)

            result = db_collection.find_one_and_replace(filter, replacement, projection, sort=sort, upsert=upsert,
                                                        return_document=ReturnDocument.BEFORE if not return_updated else ReturnDocument.AFTER)
            self._prepare_for_json(result)

        return {
            'result': result
        }

    def find_one_and_delete(self, collection, filter, projection=None, sort=None, date_fields=None):
        # type: (CollectionType, DocumentType, ProjectionOperators, SortOperators, bool, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        result = None
        if db_collection:
            self._prepare_for_mongo(filter)
            self._transform_to_datetime({'filter': filter}, date_fields)
            result = db_collection.find_one_and_delete(filter, projection, sort=sort)
            self._prepare_for_json(result)

        return {
            'result': result
        }

    def distinct(self, collection, field, filter=None, date_fields=None):
        # type: (CollectionType, str, Optional[DocumentType], DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        results = []
        if db_collection:
            self._prepare_for_mongo(filter)
            self._transform_to_datetime({'filter': filter}, date_fields)
            results = db_collection.distinct(field, filter)
            for result in results:
                self._prepare_for_json(result)

        return {
            'results': results
        }

    def aggregate(self, collection, pipeline):
        # type: (CollectionType, List[AggregationOperator]) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        if not db_collection:
            return {
                'result': [],
                'alive': False,
                'size': 0
            }

        cursor = db_collection.aggregate(pipeline)

        return self._get_cursor(cursor)

    def delete_one(self, collection, filter, date_fields=None):
        # type: (CollectionType, DocumentType, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        count = 0
        if db_collection:
            self._prepare_for_mongo(filter)
            self._transform_to_datetime({'filter': filter}, date_fields)
            count = db_collection.delete_one(filter).deleted_count
        return {
            'count': count
        }

    def delete_many(self, collection=None, filter=None, date_fields=None):
        # type: (CollectionType, DocumentType, DateFieldsType) -> Dict[str, Any]
        db_collection = self._get_collection(collection)

        count = 0
        if db_collection:
            self._prepare_for_mongo(filter)
            self._transform_to_datetime({'filter': filter}, date_fields)
            count = db_collection.delete_many(filter).deleted_count
        return {
            'count': count
        }

    def _prepare_for_json(self, doc):
        if doc:
            # convert _id from ObjectId to str representation
            if '_id' in doc:
                doc['_id'] = str(doc.pop('_id'))

            # convert all datetime fields to str representation
            self._transform_datetime_to_isostring(doc)

    def _prepare_for_mongo(self, doc):
        if doc:
            # convert json _id from str to ObjectId
            if '_id' in doc:
                if isinstance(doc['_id'], str):
                    doc['_id'] = ObjectId(doc['_id'])
                if isinstance(doc['_id'], dict):
                    for k, v in doc['_id'].items():
                        # Assume it is a shallow dict containing either str or List[str]. This corresponds to mongo query operators
                        if isinstance(v, str):
                            doc['_id'][k] = ObjectId(v)
                        else:
                            doc['_id'][k] = [ObjectId(oid) for oid in v]

    def _get_cursor(self, cursor):
        size = len(cursor._Cursor__data)
        results = []
        for _ in range(size):
            doc = cursor.next()
            self._prepare_for_json(doc)
            results.append(doc)

        # cache the cursor for later use
        # by default it will be available for 10 minutes we also
        # hash the cursor id to make random guessing a lot harder
        cursor_hash = hashlib.sha256(cursor.cursor_id + random.randint(1, 999999)).hexdigest()
        self._cursors[cursor_hash] = cursor

        return {
            'result': results,
            'size': size,
            'cursorId': cursor_hash,
            'alive': cursor.alive
        }

    def _update_response(self, upsert, replace_result=None):
        if replace_result is None:
            return {
                'matched': 0,
                'modified': 0
            }

        response = {
            'matched': replace_result.matched_count,
            'modified': replace_result.modified_count
        }

        if upsert and replace_result.upserted_id:
            response['upsertedId'] = str(replace_result.upserted_id)

        return response

    def _get_collection(self, collection=None, create=False):
        if isinstance(collection, dict):
            collection_name = collection['name']
        else:
            collection_name = collection

        if collection_name not in self._db.collection_names():
            if create:
                logger.info('Creating collection {collection} in {namespace}', collection=collection_name,
                            namespace=self._namespace)
            else:
                return None

        return self._db[collection_name]

    def _transform_to_datetime(self, document, fields):
        if fields is None:
            return

        for field in fields:
            fields = field.split('.')
            self._transform_docfield_to_datetime(document, fields)

    def _transform_docfield_to_datetime(self, doc, field):
        subdoc = doc

        for level in field[:-1]:
            if isinstance(subdoc, dict) and level in subdoc:
                subdoc = subdoc[level]
            else:
                if isinstance(subdoc, list):
                    for d in subdoc:
                        self._transform_docfield_to_datetime(d, field[1:])
                subdoc = None
                break

        if subdoc is None:
            return

        key = field[-1]

        if isinstance(subdoc, list):
            for d in subdoc:
                d[key] = parsedate(d[key]).astimezone(pytz.utc)
        else:
            subdoc[key] = parsedate(subdoc[key]).astimezone(pytz.utc)

    def _transform_datetime_to_isostring(self, document):
        if isinstance(document, dict):
            iter = document.items()
        elif isinstance(document, list):
            iter = enumerate(document)
        else:
            return

        for key, value in iter:
            if isinstance(value, datetime.datetime):
                document[key] = value.isoformat()
            else:
                self._transform_datetime_to_isostring(value)


class MongoClientWrapper:
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._client = MongoClient(host, port)
        self._namespaces = {}

    def get_namespace(self, namespace):
        if namespace not in self._namespaces.keys():
            if namespace not in self._client.database_names():
                logger.info('Creating database for {namespace}', namespace=namespace)

            db = MongoDatabaseWrapper(namespace, self._client[namespace])
            self._namespaces[namespace] = db
        else:
            db = self._namespaces[namespace]

        return db

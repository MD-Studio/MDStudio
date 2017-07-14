# -*- coding: utf-8 -*-

"""
file: db_methods.py
"""

import os
import copy
import subprocess
import logging
import datetime
import getpass

from distutils import spawn
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from autobahn import wamp
from twisted.logger import Logger

from lie_componentbase import WampSchema, validate_json_schema

logger = Logger(namespace='db')

class MongoDatabaseWrapper:
    def __init__(self, namespace, db):
        self._namespace = namespace
        self._db = db

    def count(self, collection=None, filter=None, skip=0, limit=0):
        coll = self._get_collection(collection)

        return 0 if coll is None else coll.count(filter, skip=skip, limit=limit)

    def delete_one(self, collection=None, filter=None):
        coll = self._get_collection(collection)

        return 0 if coll is None else coll.delete_one(filter).deleted_count

    def delete_many(self, collection=None, filter=None):
        coll = self._get_collection(collection)

        return 0 if coll is None else coll.delete_many(filter).deleted_count

    def find_one(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        coll = self._get_collection(collection)

        return {} if coll is None else coll.find_one(filter, projection, skip, sort=sort)

    def find_many(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        coll = self._get_collection(collection)

        if not coll:
            return []

        for doc in coll.find(filter, projection, skip, sort=sort):
            yield doc

    def insert_one(self, collection=None, insert=None):
        coll = self._get_collection(collection, True)
        return str(coll.insert_one(insert).inserted_id)

    def insert_many(self, collection=None, insert=None):
        coll = self._get_collection(collection, True)
        for id in coll.insert_many(insert).inserted_ids:
            yield str(id)

    def update_one(self, collection=None, filter=None, update=None, upsert=False):
        coll = self._get_collection(collection)

        if coll is None:
            return self._update_response(upsert, None)

        updateresult = coll.update_one(filter, update, upsert)

        return self._update_response(upsert, updateresult)

    def update_many(self, collection=None, filter=None, update=None, upsert=False):
        coll = self._get_collection(collection)

        if coll is None:
            return self._update_response(upsert, None)

        updateresult = coll.update_many(filter, update, upsert)

        return self._update_response(upsert, updateresult)

    def _update_response(self, upsert, updateresult=None):
        if updateresult is None:
            return {
                'matchedCount': 0,
                'modifiedCount': 0
            }

        response = {
            'matchedCount': updateresult.matched_count,
            'modifiedCount': updateresult.modified_count
        }

        if upsert and updateresult.upserted_id:
            response['upsertedId'] = updateresult.upserted_id

        return response

    def _get_collection(self, collection=None, create=False):
        if isinstance(collection, dict):
            collection_name = collection['name']
        else:
            collection_name = collection

        if collection_name not in self._db.collection_names():
            if create:
                logger.info('Creating collection {collection} in {namespace}', collection=collection_name, namespace=self._namespace)
            else:
                return None

        return self._db[collection_name]

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

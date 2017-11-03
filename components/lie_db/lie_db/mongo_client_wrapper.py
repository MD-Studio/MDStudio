from pymongo import MongoClient

import mdstudio.unittest.db as db
from .db_methods import logger, MongoDatabaseWrapper

class MongoClientWrapper:
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._client = self.create_mongo_client(host, port)
        self._namespaces = {}

    def get_namespace(self, namespace):
        if namespace not in self._namespaces.keys():
            if namespace not in self._client.database_names():
                logger.info('Creating database for {namespace}', namespace=namespace)

            database = MongoDatabaseWrapper(namespace, self._client[namespace])
            self._namespaces[namespace] = database
        else:
            database = self._namespaces[namespace]

        return database

    @staticmethod
    def create_mongo_client(host, port):
        if db.create_mock_client:
            import mongomock
            return mongomock.MongoClient(host, port)
        return MongoClient(host, port)

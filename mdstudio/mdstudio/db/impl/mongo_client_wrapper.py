from pymongo import MongoClient

from mdstudio.db.impl.mongo_database_wrapper import MongoDatabaseWrapper
from mdstudio.logging.logger import Logger


class MongoClientWrapper(object):
    logger = Logger()

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._client = self.create_mongo_client(host, port)
        self._databases = {}

    def get_database(self, database_name):
        if database_name not in self._databases:
            if database_name not in self._client.database_names():
                self.logger.info('Creating database "{database}"', database=database_name)

            database = MongoDatabaseWrapper(database_name, self._client[database_name])
            self._databases[database_name] = database
        else:
            database = self._databases[database_name]

        return database

    @staticmethod
    def create_mongo_client(host, port):
        try:
            
            import mdstudio.unittest.db as db
            if db.create_mock_client:
                import mongomock
                return mongomock.MongoClient(host, port)
        except Exception:
            print('Unable to create Mongo mock client on: {0} {1}'.format(host, port))

        return MongoClient(host, port)

from autobahn import wamp

from lie_componentbase import BaseApplicationSession, register, WampSchema

from .settings import SETTINGS
from .db_methods import init_mongodb

class DBWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """
    
    def __init__(self, config, **kwargs):
        BaseApplicationSession.__init__(self, config, **kwargs)
        self._databases = {}

    @register(u'liestudio.db.find', WampSchema('db', 'find/request', 1), {}, True)
    def db_find(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return collection.find_one(**request['query'])
        
    @register(u'liestudio.db.findmany', WampSchema('db', 'find/request', 1), {}, True)
    def db_findmany(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return [r for r in collection.find(**request['query'])]

    @register(u'liestudio.db.count', WampSchema('db', 'find/request', 1), {'type': 'integer'}, True)
    def db_count(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return collection.count(**request['query'])

    @register(u'liestudio.db.insert', WampSchema('db', 'insert/one', 1), WampSchema('db', 'insert/response', 1), True)
    def db_insert(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return {'inserted_ids': [str(collection.insert_one(**request['query']).inserted_id)]}

    @register(u'liestudio.db.insertmany', WampSchema('db', 'insert/many', 1), WampSchema('db', 'insert/response', 1), True)
    def db_insertmany(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return {'inserted_ids': [str(oid) for oid in collection.insert_many(**request['query']).inserted_ids]}

    @register(u'liestudio.db.update', WampSchema('db', 'update/request', 1), WampSchema('db', 'update/response', 1), True)
    def db_update(self, request, details=None):
        collection = self._get_collection(request['collection'], details)
        query = request['query']

        updateresult = collection.update_one(**query)

        response = {
            'matched_count': updateresult.matched_count,
            'modified_count': updateresult.modified_count
        }

        if query['upsert'] and updateresult.upserted_id:
            response['upserted_id'] = updateresult.upserted_id

        return response

    @register(u'liestudio.db.updatemany', WampSchema('db', 'update/request', 1), WampSchema('db', 'update/response', 1), True)
    def db_updatemany(self, request, details=None):
        collection = self._get_collection(request['collection'], details)
        query = request['query']

        updateresult = collection.update_many(**query)

        response = {
            'matched_count': updateresult.matched_count,
            'modified_count': updateresult.modified_count
        }

        if query['upsert'] and updateresult.upserted_id:
            response['upserted_id'] = updateresult.upserted_id

        return response

    @register(u'liestudio.db.delete', WampSchema('db', 'delete/request', 1), WampSchema('db', 'delete/response', 1), True)
    def db_delete(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        deleteresult = collection.delete_one(**request['query'])

        return {'deleted_count': deleteresult.deleted_count}

    @register(u'liestudio.db.deletemany', WampSchema('db', 'delete/request', 1), WampSchema('db', 'delete/response', 1), True)
    def db_deletemany(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        deleteresult = collection.delete_many(**request['query'])

        return {'deleted_count': deleteresult.deleted_count}

    def _get_db(self, dbname):
        if dbname not in self._databases.keys():
            settings = SETTINGS.copy()
            settings['dbname'] = dbname
            self._databases[dbname] = init_mongodb(settings)
            
        return self._databases[dbname]

    def _get_collection(self, collection_name, details):
        # Determine collection name from session details
        authid = details.caller_authrole if details.caller_authid is None else details.caller_authid
        
        db = self._get_db(authid)

        if not collection_name in db.collection_names():            
            self.log.info('Creating database "{0}" collection'.format(collection_name))

        return db[collection_name]

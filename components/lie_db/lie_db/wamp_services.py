from autobahn import wamp

from lie_componentbase import CoreApplicationSession, wamp_register

from .settings import SETTINGS
from .db_methods import init_mongodb

class DBWampApi(CoreApplicationSession):
    """
    Database management WAMP methods.
    """
    
    def __init__(self, config, **kwargs):
        CoreApplicationSession.__init__(self, config, **kwargs)
        self._databases = {}

    @wamp_register(u'liestudio.db.find', 'wamp://liestudio.db.schemas/find/request/v1', {}, options=wamp.RegisterOptions(details_arg='details'))
    def db_find(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return collection.find_one(**request['query'])
        
    @wamp_register(u'liestudio.db.findmany', 'wamp://liestudio.db.schemas/find/request/v1', {}, options=wamp.RegisterOptions(details_arg='details'))
    def db_findmany(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return [r for r in collection.find(**request['query'])]

    @wamp_register(u'liestudio.db.count', 'wamp://liestudio.db.schemas/find/request/v1', {'type': 'integer'}, options=wamp.RegisterOptions(details_arg='details'))
    def db_count(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return collection.count(**request['query'])

    @wamp_register(u'liestudio.db.insert', 'wamp://liestudio.db.schemas/insert/one/v1', 'wamp://liestudio.db.schemas/insert/response/v1', options=wamp.RegisterOptions(details_arg='details'))
    def db_insert(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return {'inserted_ids': [str(collection.insert_one(**request['query']).inserted_id)]}

    @wamp_register(u'liestudio.db.insertmany', 'wamp://liestudio.db.schemas/insert/many/v1', 'wamp://liestudio.db.schemas/insert/response/v1', options=wamp.RegisterOptions(details_arg='details'))
    def db_insertmany(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        return {'inserted_ids': [str(oid) for oid in collection.insert_many(**request['query']).inserted_ids]}

    @wamp_register(u'liestudio.db.update', 'wamp://liestudio.db.schemas/update/request/v1', 'wamp://liestudio.db.schemas/update/response/v1', options=wamp.RegisterOptions(details_arg='details'))
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

    @wamp_register(u'liestudio.db.updatemany', 'wamp://liestudio.db.schemas/update/request/v1', 'wamp://liestudio.db.schemas/update/response/v1', options=wamp.RegisterOptions(details_arg='details'))
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

    @wamp_register(u'liestudio.db.delete', 'wamp://liestudio.db.schemas/delete/request/v1', 'wamp://liestudio.db.schemas/delete/response/v1', options=wamp.RegisterOptions(details_arg='details'))
    def db_delete(self, request, details=None):
        collection = self._get_collection(request['collection'], details)

        deleteresult = collection.delete_one(**request['query'])

        return {'deleted_count': deleteresult.deleted_count}

    @wamp_register(u'liestudio.db.deletemany', 'wamp://liestudio.db.schemas/delete/request/v1', 'wamp://liestudio.db.schemas/delete/response/v1', options=wamp.RegisterOptions(details_arg='details'))
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

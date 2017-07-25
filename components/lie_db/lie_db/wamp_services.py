import os
from autobahn import wamp

from lie_componentbase import BaseApplicationSession, register, WampSchema
from twisted.internet.defer import inlineCallbacks, returnValue
from autobahn.wamp import SubscribeOptions, PublishOptions

from .db_methods import MongoClientWrapper, MongoDatabaseWrapper

class DBWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """
    
    def preInit(self, **kwargs):
        self.session_config_template = {}
        self.package_config_template = WampSchema('db', 'settings/settings', 1)

    def onInit(self, **kwargs):
        dbhost = os.getenv('_LIE_MONGO_HOST', self.package_config.get('dbhost', 'localhost'))
        dbport = self.package_config.get('dbport', 27017)
        self._client = MongoClientWrapper(dbhost, dbport)
        self.autolog = False
        self.autoschema = False

    @inlineCallbacks
    def onRun(self, details):
        yield self.publish(u'liestudio.db.events.online', True, options=PublishOptions(acknowledge=True))

    @wamp.register(u'liestudio.db.status')
    def db_status(self):
        return True

    @register(u'liestudio.db.findone', WampSchema('db', 'find/find-one', 1), WampSchema('db', 'find/find-response-one', 1), details_arg=True)
    @inlineCallbacks
    def db_find(self, request, details=None):
        namespace = yield self._get_namespace(request['collection'], details)

        if namespace:
            returnValue({'result': self._client.get_namespace(namespace).find_one(**request)})
        else:
            returnValue({'result': None})
        
    @register(u'liestudio.db.findmany', WampSchema('db', 'find/find-many', 1), WampSchema('db', 'find/find-response-many', 1), details_arg=True)
    @inlineCallbacks
    def db_findmany(self, request, details=None):
        namespace = yield self._get_namespace(request['collection'], details)

        if namespace:
            database = self._client.get_namespace(namespace)
            results = [r for r in database.find_many(**request)]
            returnValue({
                'result': results,
                'total': database.count(**request),
                'size': len(results)
            })
        else:
            returnValue({
                'result': [],
                'total': 0,
                'size': 0
            })

    @register(u'liestudio.db.count', WampSchema('db', 'count/count', 1), WampSchema('db', 'count/count-response', 1), details_arg=True)
    @inlineCallbacks
    def db_count(self, request, details=None):
        namespace = yield self._get_namespace(request['collection'], details)

        if namespace:
            returnValue({'total': self._client.get_namespace(namespace).count(**request)})
        else:
            returnValue({'total': 0})

    @register(u'liestudio.db.insertone', WampSchema('db', 'insert/insert-one', 1), WampSchema('db', 'insert/insert-response', 1), details_arg=True)
    @inlineCallbacks
    def db_insert(self, request, details=None):
        namespace = yield self._get_namespace(request['collection'], details)

        if namespace:
            returnValue({'ids': [self._client.get_namespace(namespace).insert_one(**request)]})
        else:
            returnValue({'ids': []})

    @register(u'liestudio.db.insertmany', WampSchema('db', 'insert/insert-many', 1), WampSchema('db', 'insert/insert-response', 1), details_arg=True)
    @inlineCallbacks
    def db_insertmany(self, request, details=None):
        namespace = yield self._get_namespace(request['collection'], details)

        if namespace:
            try:
                ids = [id for id in self._client.get_namespace(namespace).insert_many(**request)]
            except Exception as e:
                print(e)
            else:
                returnValue({'ids': ids})

        returnValue({'ids': []})

    @register(u'liestudio.db.updateone', WampSchema('db', 'update/update-request', 1), WampSchema('db', 'update/update-response', 1), details_arg=True)
    @inlineCallbacks
    def db_update(self, request, details=None):
        namespace = yield self._get_namespace(request['collection'], details)

        if namespace:
            returnValue(self._client.get_namespace(namespace).update_one(**request))
        else:
            returnValue({
                'matchedCount': 0,
                'modifiedCount': 0
            })

    @register(u'liestudio.db.updatemany', WampSchema('db', 'update/update-request', 1), WampSchema('db', 'update/update-response', 1), details_arg=True)
    @inlineCallbacks
    def db_updatemany(self, request, details=None):
        namespace = yield self._get_namespace(request['collection'], details)

        if namespace:
            returnValue(self._client.get_namespace(namespace).update_many(**request))
        else:
            returnValue({
                'matchedCount': 0,
                'modifiedCount': 0
            })

    @register(u'liestudio.db.deleteone', WampSchema('db', 'delete/delete-request', 1), WampSchema('db', 'delete/delete-response', 1), details_arg=True)
    @inlineCallbacks
    def db_delete(self, request, details=None):
        namespace = yield self._get_namespace(request['collection'], details)

        if namespace:
            returnValue({'count': self._client.get_namespace(namespace).delete_one(**request)})
        else:
            returnValue({'count': 0})

    @register(u'liestudio.db.deletemany', WampSchema('db', 'delete/delete-request', 1), WampSchema('db', 'delete/delete-response', 1), details_arg=True)
    @inlineCallbacks
    def db_deletemany(self, request, details=None):
        namespace = yield self._get_namespace(request['collection'], details)

        if namespace:
            returnValue({'count': self._client.get_namespace(namespace).delete_many(**request)})
        else:
            returnValue({'count': 0})

    @inlineCallbacks
    def _get_namespace(self, collection, details):
        authid = self._get_authid(details)

        if isinstance(collection, dict):
            # Validate permissions on namespace
            namespace = collection['namespace']
        
            # TODO: cache namespaces
            user_namespaces = yield self.call(u'liestudio.auth.namespaces', {'username': authid})
        
            if namespace not in user_namespaces:
                self.log.warn('WARNING: User {user} tried to access the {namespace} database',  user=authid, namespace=collection['namespace'])
                returnValue(None)
            else:
                returnValue('namespace-{}'.format(namespace))
        else:
            # A user is always allowed to operate on his own authid as namespace
            returnValue(authid)

    def _get_authid(self, details):
        return details.caller_authrole if details.caller_authid is None else details.caller_authid

import os
import re

from autobahn import wamp
from autobahn.wamp import SubscribeOptions, PublishOptions
from twisted.internet.defer import inlineCallbacks, returnValue

from lie_corelib import BaseApplicationSession, register, WampSchema

from .db_methods import MongoClientWrapper, MongoDatabaseWrapper

class DBWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """
    
    def preInit(self, **kwargs):
        self.session_config_template = {}
        self.package_config_template = WampSchema('db', 'settings/settings', 1)
        self.session_config['loggernamespace'] = 'db'

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

    @register(u'liestudio.db.findone', WampSchema('db', 'find/find-one-request', 1), WampSchema('db', 'find/find-one-response', 1), details_arg=True, match='prefix', scope='read')
    def db_find(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return self._client.get_namespace(namespace).find_one(**request)
        
    @register(u'liestudio.db.findmany', WampSchema('db', 'find/find-many-request', 1), WampSchema('db', 'find/find-many-response', 1), details_arg=True, match='prefix', scope='read')
    def db_findmany(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)
        database = self._client.get_namespace(namespace)

        results = [r for r in database.find_many(**request)]

        return {
            'result': results,
            'total': database.count(**request),
            'size': len(results)
        }

    @register(u'liestudio.db.count', WampSchema('db', 'count/count-request', 1), WampSchema('db', 'count/count-response', 1), details_arg=True, match='prefix', scope='read')
    def db_count(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return {'total': self._client.get_namespace(namespace).count(**request)}

    @register(u'liestudio.db.insertone', WampSchema('db', 'insert/insert-one-request', 1), WampSchema('db', 'insert/insert-one-response', 1), details_arg=True, match='prefix', scope='write')
    def db_insert(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return {'id': self._client.get_namespace(namespace).insert_one(**request)}

    @register(u'liestudio.db.insertmany', WampSchema('db', 'insert/insert-many-request', 1), WampSchema('db', 'insert/insert-many-response', 1), details_arg=True, match='prefix', scope='write')
    def db_insertmany(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        ids = [id for id in self._client.get_namespace(namespace).insert_many(**request)]
        
        return {'ids': ids}

    @register(u'liestudio.db.updateone', WampSchema('db', 'update/update-one-request', 1), WampSchema('db', 'update/update-one-response', 1), details_arg=True, match='prefix', scope='write')
    def db_update(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return self._client.get_namespace(namespace).update_one(**request)

    @register(u'liestudio.db.updatemany', WampSchema('db', 'update/update-many-request', 1), WampSchema('db', 'update/update-many-response', 1), details_arg=True, match='prefix', scope='write')
    def db_updatemany(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return self._client.get_namespace(namespace).update_many(**request)

    @register(u'liestudio.db.deleteone', WampSchema('db', 'delete/delete-one', 1), WampSchema('db', 'delete/delete-response', 1), details_arg=True, match='prefix', scope='delete')
    def db_delete(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return {'count': self._client.get_namespace(namespace).delete_one(**request)}

    @register(u'liestudio.db.deletemany', WampSchema('db', 'delete/delete-many', 1), WampSchema('db', 'delete/delete-response', 1), details_arg=True, match='prefix', scope='delete')
    def db_deletemany(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        return {'count': self._client.get_namespace(namespace).delete_many(**request)}

    def _extract_namespace(self, uri):
        return re.match('liestudio.db.\\w+\\.(.*)', uri).group(1)        

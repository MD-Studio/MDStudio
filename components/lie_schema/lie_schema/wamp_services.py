from twisted.internet.defer import DeferredLock
from autobahn import wamp
from twisted.internet.defer import inlineCallbacks, returnValue

from lie_componentbase import BaseApplicationSession, register, WampSchema

class SchemaWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """
    
    def preInit(self, **kwargs):
        self._schemas = {}
        self.lock = DeferredLock()
        self.session_config_template = {}

    def onInit(self, **kwargs):
        self.autolog = False

    @inlineCallbacks
    def onRun(self, details):
        yield self.publish(u'liestudio.schema.events.online', True, options=wamp.PublishOptions(acknowledge=True))

    @register(u'liestudio.schema.register', WampSchema('schema', 'register/register', 1), {}, details_arg=True)
    def schema_register(self, request, details=None):
        namespace = self._get_namespace(details)

        # Lock schema's resource
        self.lock.acquire()

        if namespace not in self._schemas.keys():
            self._schemas[namespace] = {}

        schemas = self._schemas[namespace]

        if request['path'] not in schemas.keys():
            schemas[request['path']] = request['schema']

            self.log.info('Stored {path} for {namespace}', path=request['path'], namespace=namespace)

            res = True
        else:
            self.log.info('Already stored {path} for {namespace}, checking equality', path=request['path'], namespace=namespace)

            # TODO: implement equality check
            res = True
            
        # Done with schema's resource, release
        self.lock.release()

        return res
        
    @register(u'liestudio.schema.get', WampSchema('schema', 'get/get', 1), {})
    def schema_get(self, request):
        namespace = request['namespace']
        path = request['path']

        # Lock schema's resource
        self.lock.acquire()

        if namespace not in self._schemas.keys():
            self._schemas[namespace] = {}

        schemas = self._schemas[namespace]

        if path in schemas.keys():
            res = schemas['path']
        else:
            self.log.error('No schema found in namespace "{}" for path "{}"'.format(namespace, path))
            res = {}
            
        # Done with schema's resource, release
        self.lock.release()

        return res

    def _get_namespace(self, details):
            # Determine collection name from session details
        authid = details.caller_authrole if details.caller_authid is None else details.caller_authid
        
        return authid

import re

from twisted.internet.defer import DeferredLock
from autobahn import wamp
from twisted.internet.defer import inlineCallbacks, returnValue

from mdstudio.application_session import BaseApplicationSession
from mdstudio.util import register, WampSchema

class SchemaWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """
    
    def preInit(self, **kwargs):
        self._schemas = {}
        self.lock = DeferredLock()
        self.session_config_template = {}
        self.session_config['loggernamespace'] = 'schema'

    def onInit(self, **kwargs):
        self.autolog = False

    @inlineCallbacks
    def onRun(self, details):
        yield self.publish(u'mdstudio.schema.endpoint.events.online', True, options=wamp.PublishOptions(acknowledge=True))

    @register(u'mdstudio.schema.endpoint.register', WampSchema('schema', 'register/register'), {}, match='prefix')
    def schema_register(self, request, details=None):
        namespace = self._extract_namespace(details.procedure)

        res = False

        # Lock schema's resource
        self.lock.acquire()

        if namespace not in self._schemas.keys():
            self._schemas[namespace] = {}

        schemas = self._schemas[namespace]

        for schema in request['schemas']:
            if schema['path'] not in schemas.keys():
                schemas[schema['path']] = schema['schema']

                self.log.info('Stored {path} for {namespace}', path=schema['path'], namespace=namespace)

                res = True
            else:
                self.log.info('Already stored {path} for {namespace}, checking equality', path=schema['path'], namespace=namespace)

                # TODO: implement equality check
                res = True
            
        # Done with schema's resource, release
        self.lock.release()

        return res
        
    @register(u'mdstudio.schema.endpoint.get', WampSchema('schema', 'get/get'), {})
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

    def _extract_namespace(self, uri):
        return re.match('mdstudio.schema.endpoint.\\w+\\.(.*)', uri).group(1)

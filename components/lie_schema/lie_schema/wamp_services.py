from autobahn import wamp

from lie_componentbase import BaseApplicationSession, register, WampSchema

class SchemaWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """
    
    def __init__(self, config, **kwargs):
        BaseApplicationSession.__init__(self, config, **kwargs)
        self._schemas = {}

    @register(u'liestudio.schema.register', WampSchema('schema', 'register', 1), {}, True)
    def schema_register(self, request, details=None):
        namespace = self._get_namespace(details)
        if namespace not in self._schemas.keys():
            self._schemas[namespace] = {}

        self._schemas[namespace][request['path']] = request['schema']

        return {}
        
    @register(u'liestudio.schema.get', WampSchema('schema', 'get', 1), {})
    def schema_get(self, request):
        namespace = request['namespace']
        path = request['path']
        if namespace not in self._schemas.keys():
            self._schemas[namespace] = {}

        schemas = self._schemas[namespace]

        if path in schemas.keys():
            return schemas['path']
        else:
            self.log.error('No schema found in namespace "{}" for path "{}"'.format(namespace, path))
            return {}

    def _get_namespace(self, details):
            # Determine collection name from session details
        authid = details.caller_authrole if details.caller_authid is None else details.caller_authid
        
        return authid

import re
from autobahn.wamp import PublishOptions


from mdstudio.api.register import register
from mdstudio.api.schema import WampSchema
from mdstudio.application_session import BaseApplicationSession
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.lock import Lock


class SchemaWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """
    
    def preInit(self, **kwargs):
        self._schemas = {}
        self.lock = Lock()
        self.session_config_template = {}
        self.session_config['loggernamespace'] = 'schema'

    def onInit(self, **kwargs):
        self.autolog = False

    @chainable
    def onRun(self, details):
        self.publish_options = PublishOptions(acknowledge=True)
        yield self.publish(u'mdstudio.schema.endpoint.events.online', True, options=self.publish_options)

    @register(u'mdstudio.schema.endpoint.upload', 'upload/v1', {})
    @chainable
    def schema_upload(self, request, auth_meta=None, **kwargs):
        vendor = auth_meta['vendor']
        component = request['component']

        res = False

        # Lock schema's resource
        yield self.lock.acquire()

        # @todo: hash and store in DB
        if vendor not in self._schemas:
            self._schemas[vendor] = {}

        if component not in self._schemas[vendor]:
            self._schemas[vendor][component] = {
                'resource': {},
                'endpoint': {}
            }

        schema_storage = self._schemas[vendor][component]

        for schema_type, schemas in request['schemas'].items():
            for schema_path, schema in schemas.items():
                if schema_path not in schema_storage:
                    schema_storage[schema_type][schema_path] = schema

                    self.log.info('Stored {path} for component {component} of {vendor}', path=schema_path, component=component, vendor=vendor)

                    res = True
                else:
                    self.log.info('Already stored {path} for component {component} of {vendor}, checking equality', path=schema_path, component=component, vendor=vendor)

                    # @todo: implement equality check
                    res = True
            
        # Done with schema's resource, release
        yield self.lock.release()

        return res

    # @todo: validate using json schema draft
    @register(u'mdstudio.schema.endpoint.get', 'get/v1', {})
    @chainable
    def schema_get(self, request, auth_meta=None):

        vendor = auth_meta['vendor']
        component = request['component']

        path = request['path']

        # Lock schema's resource
        yield self.lock.acquire()

        if vendor not in self._schemas or component not in self._schemas[vendor] or path not in self._schemas[vendor][component]:
            self.log.error('No schema found for component {} in vendor "{}" for path "{}"'.format(component, vendor, path))
            res = {}
        else:
            res = self._schemas[vendor][component][path]
            
        # Done with schema's resource, release
        yield self.lock.release()

        return res

    def authorize_request(self, uri, auth_meta):
        # @todo: check if user is part of group (in usermode)
        if auth_meta['vendor'] in auth_meta['groups']:
            return True

        # @todo: allow group/user specific access

        return False

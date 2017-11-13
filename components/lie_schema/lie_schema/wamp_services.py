from autobahn.wamp import PublishOptions

from lie_schema.exception import SchemaException
from lie_schema.schema_repository import SchemaRepository
from mdstudio.api.register import register
from mdstudio.application_session import BaseApplicationSession
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.lock import Lock
from mdstudio.deferred.return_value import return_value


class SchemaWampApi(BaseApplicationSession):
    """
    Database management WAMP methods.
    """

    def preInit(self, **kwargs):
        self._schemas = {}
        self.lock = Lock()
        self.session_config_template = {}
        self.session_config['loggernamespace'] = 'schema'

        self.endpoints = SchemaRepository(self, 'endpoints')
        self.resources = SchemaRepository(self, 'resources')
        self.claims = SchemaRepository(self, 'claims')

    def onInit(self, **kwargs):
        self.autolog = False

    @chainable
    def onRun(self, details):
        self.publish_options = PublishOptions(acknowledge=True)
        yield self.publish(u'mdstudio.schema.endpoint.events.online', True, options=self.publish_options)

    @register(u'mdstudio.schema.endpoint.upload', {}, {})
    @chainable
    def schema_upload(self, request, claims=None, **kwargs):
        vendor = claims['vendor']
        component = request['component']

        endpoint_schemas = request['schemas'].get('endpoints')
        if endpoint_schemas:
            for schema in endpoint_schemas:
                yield self.endpoints.upsert(vendor, component, schema, claims)
        resource_schemas = request['schemas'].get('resources')
        if resource_schemas:
            for schema in resource_schemas:
                yield self.resources.upsert(vendor, component, schema, claims)
        claim_schemas = request['schemas'].get('claims')
        if claim_schemas:
            for schema in claim_schemas:
                yield self.claims.upsert(vendor, component, schema, claims)

    # @todo: validate using json schema draft
    @register(u'mdstudio.schema.endpoint.get', {}, {})
    @chainable
    def schema_get(self, request, claims=None, **kwargs):
        vendor = claims['vendor']
        component = request['component']
        schema_type = request['type']
        schema_name = request['name']
        version = request.get('version', 1)

        if schema_type == "endpoints":
            res = yield self.endpoints.find_latest(vendor, component, schema_name, version)
        elif schema_type == "resources":
            res = yield self.resources.find_latest(vendor, component, schema_name, version)
        elif schema_type == "claims":
            res = yield self.claims.find_latest(vendor, component, schema_name, version)
        else:
            raise SchemaException('Schema type "{}" is not known'.format(schema_type))

        if not res:
            error = 'Schema name "{}" with type "{}", and '\
                    'version "{}" on "{}/{}" was not found'.format(vendor, component,schema_type,schema_name, version)
            raise SchemaException(error)

        return_value(res)

    def authorize_request(self, uri, claims):
        # @todo: check if user is part of group (in usermode)
        if claims['vendor'] in claims['groups']:
            return True

        # @todo: allow group/user specific access

        return False

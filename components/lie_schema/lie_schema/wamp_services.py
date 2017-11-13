import json

import hashlib
from asq.initiators import query
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

    @register(u'mdstudio.schema.endpoint.upload', 'upload/v1', {})
    @chainable
    def schema_upload(self, request, auth_meta=None, **kwargs):
        vendor = auth_meta['vendor']
        component = request['component']

        endpoint_schemas = request['schemas'].get('endpoints')
        if endpoint_schemas:
            for schema in endpoint_schemas:
                yield self.endpoints.upsert(vendor, component, schema, auth_meta)
        resource_schemas = request['schemas'].get('resources')
        if resource_schemas:
            for schema in resource_schemas:
                yield self.resources.upsert(vendor, component, schema, auth_meta)
        claim_schemas = request['schemas'].get('claims')
        if claim_schemas:
            for schema in claim_schemas:
                yield self.claims.upsert(vendor, component, schema, auth_meta)

    # @todo: validate using json schema draft
    @register(u'mdstudio.schema.endpoint.get', 'get/v1', {})
    @chainable
    def schema_get(self, request, auth_meta=None):
        vendor = auth_meta['vendor']
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
            raise SchemaException('Schema name "{}" with type "{}", and version "{}" on "{}/{}" was not found'.format(vendor, component, schema_type, schema_name, version))

        return_value(res)

    def authorize_request(self, uri, auth_meta):
        # @todo: check if user is part of group (in usermode)
        if auth_meta['vendor'] in auth_meta['groups']:
            return True

        # @todo: allow group/user specific access

        return False
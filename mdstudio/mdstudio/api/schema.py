import re
import os

import jsonschema
import json

from jsonschema import FormatChecker, ValidationError

from mdstudio.api.singleton import Singleton
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


class ISchema:
    def __init__(self):
        self.cached = {}

    def _retrieve_local(self, base_path, schema_path, versions=None):
        if versions:
            if not isinstance(versions, list):
                versions = [versions]

            for version in versions:
                path = os.path.join(base_path, '{}.v{}.json'.format(schema_path, version))

                with open(path, 'r') as f:
                    self.cached[version] = json.load(f)
        else:
            path = os.path.join(base_path, '{}.json'.format(schema_path))

            with open(path, 'r') as f:
                self.cached[0] = json.load(f)

    @chainable
    def _recurse_subschemas(self, schema, session):
        success = True

        if isinstance(schema, dict):
            ref = schema.pop('$ref', None)

            if ref:
                ref_decomposition = re.match(r'(\w+)://(.+)', ref)
                subschema = self._schema_factory(ref_decomposition.group(1), ref_decomposition.group(2))

                if (yield subschema.flatten(session)):
                    schema.update(subschema.to_schema())
                else:
                    success = False

            if success:
                for k, v in schema.items():
                    recursed = yield self._recurse_subschemas(v, session)

                    if not recursed['success']:
                        success = False
                        break

                    schema[k] = recursed['schema']
        elif isinstance(schema, list):
            for v in schema:
                success = success and (yield self._recurse_subschemas(v, session))['success']

        return_value({
            'schema': schema,
            'success': success
        })

    @staticmethod
    def _schema_factory(schema_type, schema_path):
        factory_dict = {
            'resource': lambda p: ResourceSchema('resource://{}'.format(p)),
            'endpoint': lambda p: EndpointSchema('endpoint://{}'.format(p)),
            'https': lambda p: HttpsSchema('https://{}'.format(p)),
            'http': lambda p: HttpsSchema('https://{}'.format(p))
        }

        return factory_dict[schema_type](schema_path)

    def to_schema(self):
        if not self.cached:
            raise NotImplementedError("This schema has not been or could not be retrieved.")

        if len(self.cached.items()) > 1:
            return {
                'oneOf': self.cached.values()
            }
        else:
            for k, v in self.cached.items():
                return v


class InlineSchema(ISchema):
    def __init__(self, schema):
        self.schema = schema

    def flatten(self, session=None):
        return self._recurse_subschemas(self.schema, session)

    def to_schema(self):
        return self.schema

class HttpsSchema(ISchema):
    def __init__(self, uri):
        super(HttpsSchema, self).__init__()
        self.uri = uri

    def flatten(self, session=None):
        return True

    def to_schema(self):
        return {'$ref': self.uri}


class EndpointSchema(ISchema):
    def __init__(self, uri, versions=None):
        super(EndpointSchema, self).__init__()
        uri_decomposition = re.match(r'endpoint://([\w/_\-]+?)/?((v\d+,?)*)?$', uri)
        self.schema_path = uri_decomposition.group(1)

        uri_versions = uri_decomposition.group(2)
        self.versions = versions or ([int(v) for v in uri_versions.replace('v', '').split(',')] if uri_versions else [1])

        self.schema_subdir = 'endpoints'

    @chainable
    def flatten(self, session=None):
        # type: (CommonSession) -> bool
        if self.cached:
            return_value(True)

        self._retrieve_local(os.path.join(session.component_schemas_path(), self.schema_subdir), self.schema_path, self.versions)

        success = True

        for version, schema in self.cached.items():
            flattened = yield self._recurse_subschemas(schema, session)
            self.cached[version] = flattened['schema']

            if not flattened['success']:
                success = False
                break

        return_value(success)


class ClaimSchema(EndpointSchema):
    def __init__(self, uri, versions=None):
        super(ClaimSchema, self).__init__(uri, versions)
        self.schema_subdir = 'claims'


class MDStudioClaimSchema(metaclass=Singleton):
    def __init__(self, session):
        with open(os.path.join(session.mdstudio_schemas_path(), 'claims.json'), 'r') as base_claims_file:
            self.schema = json.load(base_claims_file)

    def to_schema(self):
        return self.schema


class ResourceSchema(ISchema):
    def __init__(self, uri, versions=None):
        super(ResourceSchema, self).__init__()
        uri_decomposition = re.match(r'resource://([\w\d_\-]+)/([\w\d_\-]+)/([\w/_\-]+?)/?((v\d+,?)*)?$', uri)
        self.vendor = uri_decomposition.group(1)
        self.component = uri_decomposition.group(2)
        self.schema_path = uri_decomposition.group(3)

        self.versions = versions or [int(v) for v in uri_decomposition.group(4).replace('v', '').split(',')] or [1]

    @chainable
    def flatten(self, session=None):
        # type: (CommonSession) -> bool
        if self.cached:
            return_value(True)

        if session.component_config.static.vendor == self.vendor and session.component_config.static.component == self.component:
            self._retrieve_local(os.path.join(session.component_schemas_path(), 'resources'), self.schema_path, self.versions)
        else:
            yield self._retrieve_wamp(session)

        success = True

        for version, schema in self.cached.items():
            flattened = yield self._recurse_subschemas(schema, session)
            self.cached[version] = flattened['schema']

            if not flattened['success']:
                success = False
                break

        return_value(success)

    @chainable
    def _retrieve_wamp(self, session):
        for version in self.versions:
            self.cached[version] = yield session.call('mdstudio.schema.endpoint.get', {
                'name': self.schema_path,
                'version': version,
                'component': self.component,
                'type': 'resource'
            }, claims={
                'vendor': self.vendor
            })

def validate_json_schema(schema_def, instance):
    jsonschema.validate(instance, schema_def, format_checker=FormatChecker())

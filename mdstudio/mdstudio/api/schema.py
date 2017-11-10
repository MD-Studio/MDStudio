import re
import os

import jsonschema
import json

from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


class Schema:
    def __init__(self, uri, versions=None):
        # type: (str, Optional[List[Union[int, str]]]) -> None
        schema_uri_match = re.match('(\\w+)://(.+)(\\.json)?', uri)
        transport = schema_uri_match.group(1)
        schema_path = schema_uri_match.group(2)

        if not versions:
            versions = []

        self.uri = uri
        self.transport = transport
        self.versions = []
        self.cached = {}

        if transport.startswith('http'):
            self.cached = {'v1': {'$ref': uri}}

        for version in versions:
            if isinstance(version, int):
                self.versions.append('v{}'.format(version))
            elif isinstance(version, str):
                self.versions.append(version)
            else:
                raise TypeError

        versions_match = re.match('(.*)/((v[0-9]+,?)+)', schema_path)
        if versions_match:
            self.schema_path = versions_match.group(1)
            self.versions.extend(versions_match.group(2).split(','))
        else:
            self.schema_path = schema_path

        if len(self.versions) == 0 and not (transport.startswith('http') or transport == 'mdstudio'):
            self.versions.append('v1')

    @chainable
    def flatten(self, session):
        # type: (BaseApplicationSession) -> None
        if self.cached:
            return_value(True)

        if self.transport == 'mdstudio':
            self._retrieve_local(os.path.join(session.component_info['mdstudio_lib_path'], 'schema'))
        elif self.transport == 'endpoint':
            self._retrieve_local(os.path.join(session.component_info['module_path'], 'schema', 'endpoints'))
        elif self.transport == 'resource':
            self._retrieve_local(os.path.join(session.component_info['module_path'], 'schema', 'resources'))
        elif self.transport == 'local':
            self._retrieve_local(os.path.join(session.component_info['module_path'], 'schema', 'local'))
        elif self.transport == 'wamp':
            yield self._retrieve_wamp(session)
        elif self.transport.startswith('http'):
            yield self._retrieve_http()
        else:
            return_value(False)

        success = True

        for version, schema in self.cached.items():
            flattened = yield self._recurse_subschemas(schema, session)
            self.cached[version] = flattened['schema']

            success = success and flattened['success']
            if not success:
                break;

        return_value(success)

    @chainable
    def _recurse_subschemas(self, schema, session):
        success = True

        if isinstance(schema, dict):
            ref = schema.pop('$ref', None)

            if ref:
                subschema = Schema(ref)

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



    def _retrieve_local(self, base_path):
        if self.versions:
            for version in self.versions:
                path = os.path.join(base_path, '{}.{}.json'.format(self.schema_path, version))
                with open(path, 'r') as f:
                    self.cached[version] = json.load(f)
        else:
            path = os.path.join(base_path, '{}.json'.format(self.schema_path))
            with open(path, 'r') as f:
                self.cached['v1'] = json.load(f)

    @chainable
    def _retrieve_wamp(self, session):
        schema_path_match = re.match('(.*?)\\.(.*?)\\.(.*?)\\.(.*?)', self.schema_path)
        vendor = schema_path_match.group(1)
        component = schema_path_match.group(2)
        schema_type = schema_path_match.group(3)
        schema_path = schema_path_match.group(4)

        for version in self.versions:
            self.cached[version] = yield session.call('mdstudio.schema.get', {
                'name': schema_path,
                'version': version,
                'component': component,
                'type': schema_type
            }, {
                'vendor': vendor
            })

    def _retrieve_http(self):
        # @todo: possibly cache this
        self.cached['v1'] = {'$ref': self.uri}

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

# @todo: enable validation
def validate_output(output_schema):
    def wrap_f(f):
        @chainable
        def wrapped_f(self, request, **kwargs):
            if isinstance(output_schema, Schema):
                yield output_schema.flatten()
                schema = output_schema.to_schema()
            else:
                schema = output_schema

            res = yield f(self, request, **kwargs)

            validate_json_schema(self, schema, res)

            return_value(res)

        return wrapped_f

    return wrap_f


def validate_input(input_schema, strict=True):
    def wrap_f(f):
        @chainable
        def wrapped_f(self, request, **kwargs):
            if isinstance(input_schema, Schema):
                yield input_schema.flatten()
                schema = input_schema.to_schema()
            else:
                schema = input_schema

            valid = validate_json_schema(self, schema, request)

            if strict and not valid:
                return_value({'error': 'Input not matching schema'})
            else:
                res = yield f(self, request, **kwargs)

                return_value(res)

        return wrapped_f

    return wrap_f


def validate_json_schema(session, schema_def, request):
    # try:
    jsonschema.validate(request, schema_def)
    # except Exception as e:
    #     session.log.error('Error validating json schema: {error}', error=error)
    #     return False

    return True

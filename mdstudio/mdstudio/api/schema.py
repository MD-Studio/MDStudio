import re
import os

import jsonschema
import json

from jsonschema import FormatChecker, ValidationError

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
            'resource': lambda p: ResourceSchema(p),
            'endpoint': lambda p: EndpointSchema(p),
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
        print(uri_decomposition.groups())
        self.schema_path = uri_decomposition.group(1)

        uri_versions = uri_decomposition.group(2)
        self.versions = versions or ([int(v) for v in uri_versions.replace('v', '').split(',')] if uri_versions else [1])

    @chainable
    def flatten(self, session=None):
        # type: (CommonSession) -> bool
        if self.cached:
            return_value(True)

        self._retrieve_local(os.path.join(session.component_schemas_path, 'endpoints'), self.schema_path, self.versions)

        success = True

        for version, schema in self.cached.items():
            flattened = yield self._recurse_subschemas(schema, session)
            self.cached[version] = flattened['schema']

            if not flattened['success']:
                success = False
                break

        return_value(success)


class ResourceSchema(ISchema):
    def __init__(self, uri, versions=None):
        super(ResourceSchema, self).__init__()
        uri_decomposition = re.match(r'resource://([\w\d_\-]+)/([\w\d_\-]+)/([\w/_\-]+?)/?((v\d+,?)*)', uri)
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
            self._retrieve_local(os.path.join(session.component_schemas_path, 'endpoints'), self.schema_path, self.versions)
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


# @todo: enable validation
def validate_output(output_schema):
    def wrap_f(f):
        if not output_schema:
            # print("Output is not checked because schema is {}".format(output_schema))
            return f

        @chainable
        def wrapped_f(self, request, **kwargs):
            if isinstance(output_schema, ISchema):
                yield output_schema.flatten(self)
                schema = output_schema.to_schema()
            else:
                schema = output_schema

            res = yield f(self, request, **kwargs)

            if 'result' in res:
                try:
                    validate_json_schema(schema, res['result'])
                except ValidationError as e:
                    self.log.error(e)
                    return_value({'error': 'Something went wrong inside the component. Contact the developer.'})

            return_value(res)

        return wrapped_f

    return wrap_f


def validate_input(input_schema, strict=True):
    def wrap_f(f):
        if not input_schema:
            # print("Input is not checked because schema is {}".format(input_schema))
            return f

        @chainable
        def wrapped_f(self, request, **kwargs):
            if isinstance(input_schema, ISchema):
                yield input_schema.flatten(self)
                schema = input_schema.to_schema()
            else:
                schema = input_schema

            try:
                validate_json_schema(schema, request)
            except ValidationError as e:
                if strict:
                    return_value({'error': 'Input not matching schema'})
            else:
                res = yield f(self, request, **kwargs)

                return_value(res)

        return wrapped_f

    return wrap_f


def validate_json_schema(schema_def, instance):
    jsonschema.validate(instance, schema_def, format_checker=FormatChecker())

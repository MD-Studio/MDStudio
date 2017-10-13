# coding=utf-8
import json
from typing import *

import jsonschema
import os
import re
from autobahn import wamp
from twisted.internet.defer import inlineCallbacks, returnValue

from .config.handler import ConfigHandler
from .logging import block_on

# add unicode placeholder for PY3
try:
    unicode('')
except NameError as e:
    class unicode(str):
        def __init__(self, obj='', *args, **kwargs):
            super(unicode, self).__init__(u'{}'.format(obj), *args, **kwargs)


def resolve_config(config):
    """
    Resolve the config as dictionary

    Check if input type is a dictionary, return.
    Check if the input type is a valid file path to a JSON configuration file,
    load as dictionary.

    This function always returns a dictionary, empty or not.

    :param config: package configuration to resolve
    :type config:  mixed
    :return:       configuration
    :rtype:        :py:dict
    """

    settings = {}
    if config:
        if type(config) in (dict, ConfigHandler):
            return config

        if type(config) in (str, unicode):
            config = os.path.abspath(config)
            if os.path.isfile(config):
                with open(config) as cf:
                    try:
                        settings = json.load(cf)
                    except BaseException:
                        pass

    return settings


def extend_with_default(validator_class, session):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for prperty, subschema in properties.items():
            if "default" in subschema and prperty not in instance.keys():
                session.log.warn(
                    'WARNING: during json schema validation, {} was not present in the instance, setting to default'.format(
                        prperty))
                instance.setdefault(prperty, subschema["default"])

        for error in validate_properties(
                validator, properties, instance, schema,
        ):
            yield error

    return jsonschema.validators.extend(
        validator_class, {"properties": set_defaults},
    )


class WampSchemaHandler:
    def __init__(self, session):
        self.corelib_path = session.component_info.get('corelib_path')
        self.package_name = session.component_info.get('package_name')
        self.session = session
        self.cache = {}

    def handler(self, uri):
        if uri not in self.cache.keys():
            res = block_on(self.resolve(uri))
            self.cache[uri] = res
        else:
            res = self.cache[uri]

        return res

    @inlineCallbacks
    def resolve(self, uri):
        schema_path_match = re.match('wamp://mdstudio\.schema\.get/([a-z_]+)/(.+)', uri)
        if not schema_path_match:
            self.session.log.error("Not a proper wamp uri")

        schema_namespace = schema_path_match.group(1)
        schema_path = schema_path_match.group(2)

        if 'lie_{}'.format(schema_namespace) == self.package_name:
            res = self.session.get_schema(schema_path)
        elif schema_namespace == 'mdstudio':
            res = self.session.get_schema(schema_path, self.corelib_path)
        else:
            res = yield self.session.call(u'mdstudio.schema.endpoint.get', {'namespace': schema_namespace, 'path': schema_path})

        if res is None:
            self.session.log.warn('WARNING: could not retrieve a valid schema')
            res = {}

        returnValue(res)


def validate_json_schema(session, schema_def, request):
    if not isinstance(schema_def, ISchema):
        schema_def = InlineSchema(schema_def)

    valid = False

    for schema in schema_def.schemas():
        resolver = jsonschema.RefResolver.from_schema(schema, handlers={'wamp': session.wamp_schema_handler.handler})

        DefaultValidatingDraft4Validator = extend_with_default(jsonschema.Draft4Validator, session)
        validator = DefaultValidatingDraft4Validator(schema, resolver=resolver)

        errors = sorted(validator.iter_errors(request), key=lambda x: x.path)

        if len(errors) == 0:
            valid = True
            break
        else:
            for error in errors:
                session.log.error('Error validating json schema: {error}', error=error)

    return valid


class ISchema:
    def __str__(self):
        raise NotImplementedError('Subclass should implement this')

    def schemas(self):
        raise NotImplementedError('Subclass should implement this')


class Schema(ISchema):
    def __init__(self, url, transport='http'):
        self.schema_uri = '{}://{}'.format(transport, url)

    def __str__(self):
        return self.schema_uri

    def schemas(self):
        yield {'$ref': self.schema_uri}


class WampSchema(ISchema):
    def __init__(self, namespace, path, versions=None):
        # type: (str, str, Optional[Union[List[int],Set[int]]]) -> None
        if versions is None:
            versions = [1]

        self.namespace = namespace
        self.path = path
        self.versions = [int(v) for v in versions]

        self.url_format = 'wamp://mdstudio.schema.get/{}/{}'

    def __str__(self):
        return self.url_format.format('{}', '{}.{}') \
            .format(self.namespace, self.path, ['v{}'.format(v) for v in self.versions])

    def paths(self):
        for version in self.versions:
            yield '{}.v{}'.format(self.path, int(version))

    def uris(self):
        for path in self.paths():
            yield self.url_format.format(self.namespace, path)

    def schemas(self):
        for uri in self.uris():
            yield {'$ref': uri}


class InlineSchema(ISchema):
    def __init__(self, schema):
        self.schema = schema

    def __str__(self):
        return str(self.schema.items() if isinstance(self.schema, dict) else self.schema)

    def schemas(self):
        yield self.schema if isinstance(self.schema, dict) else {'$ref': self.schema}


def validate_output(output_schema):
    if not isinstance(output_schema, ISchema):
        # If the schema is not a subclass of ISchema, try to create an inline schema
        output_schema = InlineSchema(output_schema)

    def wrap_f(f):
        @inlineCallbacks
        def wrapped_f(self, request, **kwargs):
            res = yield f(self, request, **kwargs)

            validate_json_schema(self, output_schema, res)

            returnValue(res)

        return wrapped_f

    return wrap_f


def validate_input(input_schema, strict=True):
    if not isinstance(input_schema, ISchema):
        # If the schema is not a subclass of ISchema, try to create an inline schema
        input_schema = InlineSchema(input_schema)

    def wrap_f(f):
        @inlineCallbacks
        def wrapped_f(self, request, **kwargs):
            valid = validate_json_schema(self, input_schema, request)

            if strict and not valid:
                returnValue({})
            else:
                res = yield f(self, request, **kwargs)

                returnValue(res)

        return wrapped_f

    return wrap_f


def register(uri, input_schema, output_schema, match=None, options=None, scope=None):
    # type: (str, ISchema, ISchema, bool, Optional[str], Optional[wamp.RegisterOptions], Optional[str]) -> function
    """
    Decorator for more complete WAMP uri registration

    Besides registering the uri, also wrap the function to validate json schemas on input and output.
    Store the schema definition and custom scopes in attributes of the function for later processing.

    :param uri:             WAMP uri to register on
    :type uri:              str
    :param input_schema:    JSON schema to check the input.
    :type input_schema:     ISchema
    :param output_schema:   JSON schema to check the output.
    :type output_schema:    ISchema
    :param details_arg:     Boolean indicating whether the wrapped function expects a details argument 
                            (will be set in the RegisterOptions).
    :type details_arg:      bool
    :param match:           Matching approach for the uri. Defaults to 'exact' in crossbar.
    :type match:            str
    :param options:         Options for registration. Created if not provided.
    :type options:          wamp.RegisterOptions
    :param scope:           Custom scope name within this namespace. If none is provided, only exact uri permission grants access.
    :type scope:            str
    :return:                Wrapped function with extra attributes
    :rtype:                 function
    """

    if options is None:
        # If options is not given but required for match or details, create it
        options = wamp.RegisterOptions()

    if not options.details_arg:
        options.details_arg = 'details'

    if match:
        options.match = match

    def wrap_f(f):
        @wamp.register(uri, options)
        @validate_input(input_schema)
        @validate_output(output_schema)
        @inlineCallbacks
        def wrapped_f(self, request, *args, **kwargs):
            res = yield f(self, request, *args, **kwargs)

            returnValue(res)

        wrapped_f._lie_input_schema = input_schema
        wrapped_f._lie_output_schema = output_schema

        if scope:
            wrapped_f._lie_uri = uri
            wrapped_f._lie_scope = scope

        return wrapped_f

    return wrap_f

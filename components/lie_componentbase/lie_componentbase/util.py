import inspect
import json
import sys
import os
import re

from twisted.internet.defer import TimeoutError, inlineCallbacks, returnValue
from twisted.python.failure import Failure
from autobahn               import wamp
import jsonschema

from .config.config_handler import ConfigHandler
from .config import PY3

if PY3:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty

# add unicode placeholder for PY3
try:
    unicode('')
except NameError as e:
    class unicode(str):
        def __init__(self, object='', *args, **kwargs):
            super(unicode, self).__init__(u'{}'.format(object), *args, **kwargs)


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

def block_on(d, timeout=None):
    q = Queue()
    d.addBoth(q.put)
    try:
        ret = q.get(timeout is not None, timeout)
    except Empty:
        raise TimeoutError
    if isinstance(ret, Failure):
        ret.raiseException()
    else:
        return ret

def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema and property not in instance.keys():
                print('WARNING: during json schema validation, {} was not present in the instance, setting to default'.format(property))
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(
            validator, properties, instance, schema,
        ):
            yield error

    return jsonschema.validators.extend(
        validator_class, {"properties" : set_defaults},
    )

DefaultValidatingDraft4Validator = extend_with_default(jsonschema.Draft4Validator)


class WampSchemaHandler:
    def __init__(self, session):
        self.componentbase_path = session.component_info.get('componentbase_path')
        self.package_name = session.component_info.get('package_name')
        self.session = session
        self.cache = {}
    
    def handler(self, uri):
        if uri not in self.cache.keys():
            res = block_on(self.resolve(uri))
            self.cache[uri]=res
        else:
            res = self.cache[uri]

        return res

    
    @inlineCallbacks
    def resolve(self, uri):
        schema_path_match = re.match('wamp://liestudio\.schema\.get/([a-z_]+)/(.+)', uri)
        if not schema_path_match:
            self.session.log.error("Not a proper wamp uri")
            
        schema_namespace = schema_path_match.group(1)
        schema_path = schema_path_match.group(2)
        
        if 'lie_{}'.format(schema_namespace) == self.package_name:
            res = self.session.get_schema(schema_path)
        elif 'lie_{}'.format(schema_namespace) == 'lie_componentbase':
            res = self.session.get_schema(schema_path, self.componentbase_path)
        else:
            res = yield self.session.call(u'liestudio.schema.get', {'namespace': schema_namespace, 'path': schema_path})

        if res is None:
            self.session.log.warn('WARNING: could not retrieve a valid schema')
            res = {}
        
        returnValue(res)

def validate_json_schema(session, schema_def, request):
    if not isinstance(schema_def, (Schema, WampSchema, InlineSchema)):
        schema_def = InlineSchema(schema_def)

    valid = False
    
    for schema in schema_def.schemas():
        resolver = jsonschema.RefResolver.from_schema(schema, handlers={'wamp': session.wamp_schema_handler.handler})
        validator=DefaultValidatingDraft4Validator(schema, resolver=resolver)
        
        try:
            validator.validate(request)
            valid = True
        except jsonschema.ValidationError as e:
            session.log.error(e.message)

        if valid:
            break

    return valid

class Schema:
    def __init__(self, url, transport='http'):
        self.schema_uri = '{}://{}'.format(transport, url)

    def __str__(self):
        return self.schema_uri

    def schemas(self):
        yield {'$ref': self.schema_uri}

class WampSchema:
    def __init__(self, namespace, path, versions):
        if not isinstance(versions, list):
            versions = [versions]

        self.namespace = namespace
        self.path = path
        self.versions = [int(v) for v in versions]

        self.url_format = 'wamp://liestudio.schema.get/{}/{}'

    def __str__(self):
        return self.url_format.format('{}', '{}/{}') \
                              .format(self.namespace, self.path, ['v{}'.format(v) for v in self.versions])

    def paths(self):
        for version in self.versions:
            yield '{}/v{}'.format(self.path, int(version))

    def uris(self):
        for path in self.paths():
            yield self.url_format.format(self.namespace, path)

    def schemas(self):
        for uri in self.uris():
            yield {'$ref': uri}

class InlineSchema:
    def __init__(self, schema):
        self.schema = schema

    def __str__(self):
        return str(self.schema.items() if isinstance(self.schema, dict) else self.schema)

    def schemas(self):
        yield self.schema if isinstance(self.schema, dict) else {'$ref': self.schema}
    
def register(uri, input_schema, output_schema, details_arg=False, options=None):
    if not isinstance(input_schema, (Schema, WampSchema, InlineSchema)):
        input_schema = InlineSchema(input_schema)

    if not isinstance(output_schema, (Schema, WampSchema, InlineSchema)):
        output_schema = InlineSchema(output_schema)

    if details_arg:
        if options is None:
            options = wamp.RegisterOptions(details_arg='details')
        else:
            options.details_arg = 'details'

    def wrap_f(f):
        @wamp.register(uri, options)
        @inlineCallbacks
        def wrapped_f(self, request, **kwargs):
            self.log.info('DEBUG: validating input with schema {}'.format(input_schema))
            if not validate_json_schema(self, input_schema, request):
                returnValue({})
            else:
                res = yield f(self, request, **kwargs)
        
                valid = validate_json_schema(self, output_schema, res)
                
                returnValue(res)

        wrapped_f._lie_input_schema = input_schema
        wrapped_f._lie_output_schema = output_schema

        return wrapped_f
    
    return wrap_f
import json
import sys
import os

from twisted.internet.defer import TimeoutError, inlineCallbacks, returnValue
from twisted.python.failure import Failure
from autobahn               import wamp
import jsonschema

from .config.config_handler import ConfigHandler

# Retrieve python version
PYVERSION = sys.version_info
PY2 = PYVERSION < (3, 0)
PY3 = PYVERSION >= (3, 0)

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
    :return:               configuration
    :rtype:                dict
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

def wamp_schema_handler(session):
    def handler(uri):
        @inlineCallbacks
        def resolve(uri):
            module_name = session.__module__.split('.')[0]
            schema_path_match = re.match('wamp://liestudio\.([a-z]+)\.schemas/(.+)', uri)
            if not schema_path_match:
                session.log.error("Not a proper wamp uri")
                
            # schema_path_groups = schema_path_groups.groups()
            schema_path = schema_path_match.group(2)
            
            if 'lie_{}'.format(schema_path_match.group(1)) == module_name:
                res = yield session.get_schema(schema_path)
            elif 'lie_{}'.format(schema_path_match.group(1)) == 'lie_system':
                res = yield session.get_schema(schema_path, os.path.dirname(inspect.getfile(LieApplicationSession)))
            else:
                res = yield session.call(u'liestudio.{}.schemas', schema_path)

            if res is None:
                self.log.warn('WARNING: could not retrieve a valid schema')
                res = {}
            
            returnValue(res)

        return block_on(resolve(uri))

    return handler

def validate_json_schema(session, schema_def, request):
    schema = {'$ref': schema_def} if type(schema_def) in (str, unicode) else schema_def
    
    resolver = jsonschema.RefResolver.from_schema(schema, handlers={'wamp': wamp_schema_handler(session)})
    validator=DefaultValidatingDraft4Validator(schema, resolver=resolver)
    
    valid = True
    try:
        validator.validate(request)
    except jsonschema.ValidationError as e:
        session.log.error(e.message)
        valid = False

    return valid
    
def wamp_register(uri, input_schema, output_schema, options=None):
    def wrap_f(f):
        @wamp.register(uri, options)
        @inlineCallbacks
        def wrapped_f(self, request, **kwargs):
            self.log.info('DEBUG: validating input with schema {}'.format(input_schema))
            if not validate_json_schema(self, input_schema, request):
                res = yield {}
                returnValue(res)

            res = yield f(self, request, **kwargs)
        
            self.log.debug('DEBUG: validating output with schema {}'.format(output_schema))
            validate_json_schema(self, output_schema, res)
            
            returnValue(res)

        return wrapped_f
    
    return wrap_f

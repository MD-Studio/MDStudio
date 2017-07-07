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

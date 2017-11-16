# coding=utf-8
import json

import os

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
        # if type(config) in (dict, ConfigHandler):
        if isinstance(config, dict):
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
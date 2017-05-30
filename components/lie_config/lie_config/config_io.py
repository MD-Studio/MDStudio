# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys
import os
import collections
import json
import StringIO

PY3 = sys.version_info.major == 3
if PY3:
    import configparser
else:
    import ConfigParser as configparser

from twisted.logger import Logger

logging = Logger()


def _open_anything(source, mode='r'):
    """
    Open input available from a file, a Python file like object, standard
    input, a URL or a string and return a uniform Python file like object
    with standard methods.

    :param source: Input as file, Python file like object, standard
                   input, URL or a string
    :type source:  mixed
    :param mode:   file access mode, defaults to 'r'
    :type mode:    string
    :return:       Python file like object
    """

    # Check if the source is a file and open
    if os.path.isfile(source):
        logging.debug('Reading file from disk {0}'.format(source))
        return open(source, mode)

    # Check if source is file already openend using 'open' or 'file' return
    if hasattr(source, 'read'):
        logging.debug('Reading file {0} from file object'.format(source.name))
        return source

    # Check if source is standard input
    if source == '-':
        logging.debug('Reading file from standard input')
        return sys.stdin

    else:
        # Check if source is a URL and try to open
        try:

            import urllib2
            import urlparse
            if urlparse.urlparse(source)[0] == 'http':
                result = urllib2.urlopen(source)
                logging.debug("Reading file from URL with access info:\n {0}".format(result.info()))
                return result
        except BaseException:
            logging.info("Unable to access URL")

        # Check if source is file and try to open else regard as string
        try:
            return open(source)
        except BaseException:
            logging.debug("Unable to access as file, try to parse as string")
            return StringIO.StringIO(str(source))


def _flatten_nested_dict(config, parent_key='', sep='.'):
    """
    Flatten a nested dictionary by concatenating all
    nested keys.
    Keys are converted to a string representation if
    needed.

    :param config:     dictionary to flatten
    :type config:      :py:class:`dict`
    :param parent_key: leading string in concatenated keys
    :type parent_key:  str
    :param sep:        concatenation seperator
    :type sep:         str
    :return:           flattened dictionary
    :rtype:            :py:class:`dict`
    """

    items = []
    for key, value in config.items():

        # parse key to string if needed
        if type(key) not in (str, unicode):
            logging.debug('Dictionary key {0} of type {1}. Parse to unicode'.format(key, type(key)))
            key = unicode(key)

        new_key = unicode(parent_key + sep + key if parent_key else key)
        if isinstance(value, collections.MutableMapping):
            items.extend(_flatten_nested_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))

    return dict(items)


def _nest_flattened_dict(config, sep='.'):
    """
    Convert a dictionary that has been flattened by the
    `_flatten_nested_dict` method to a nested representation

    :param config:     dictionary to nest
    :type config:      :py:class:`dict`
    :param sep:        concatenation seperator
    :type sep:         str
    :return:           nested dictionary
    :rtype:            :py:class:`dict`
    """

    nested_dict = {}
    for key, value in config.items():

        splitted = key.split(sep)
        if len(splitted) == 1:
            nested_dict[key] = value

        d = nested_dict
        for k in splitted[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]

        d[splitted[-1]] = value

    return nested_dict


def config_from_ini(inifile):
    """
    Read configuration from a .ini or .cfg style configuration file.
    An IOError is raised when the configuration could not be parsed.

    :param inifile: configuration to be parsed
    :type inifile:  any type accepted by _open_anything function

    :return:        parsed configuration
    :rtype:         :py:class:`dict`
    """

    fileobject = _open_anything(inifile)
    filecontent = fileobject.read()

    if not len(filecontent):
        raise IOError('INI style configuration could not be read.')

    c = configparser.ConfigParser()
    c.readfp(StringIO.StringIO(filecontent.decode('utf8')))

    config = {}
    for section in c.sections():
        config[section] = {}
        for param in c.options(section):
            value = c.get(section, param)

            if '.' in value:
                try:
                    value = c.getfloat(section, param)
                except BaseException:
                    pass
            else:
                try:
                    value = c.getint(section, param)
                except BaseException:
                    pass

            try:
                value = c.getboolean(section, param)
            except BaseException:
                pass
            config[section][param] = value

    return config


def config_to_ini(config, tofile):
    """
    Export configuration to .ini or .cfg style configuration file.

    .. warning:: This makes use of the ConfigParser.read_dict method only
                 available in Python version 3.2 and higher.

    :param config: configuration to export
    :type config:  ConfigHandler instance
    :param tofile: path of .ini or .cfg file to export to.
    :type tofile:  string
    """
    if not PY3:
        raise IOError('Configuration export to INI style configuration file only supported in Python version >= 3.2')

    nested_dict = _nest_flattened_dict(config())

    c = configparser.ConfigParser()
    c.read_dict(nested_dict)

    with open(tofile, 'w') as inifile:
        inifile.write(c)


def config_from_json(jsonfile):
    """
    Import configuration from a JSON file or string

    :param inifile: configuration to be parsed
    :type inifile:  any type accepted by _open_anything function

    :return:        parsed configuration
    :rtype:         :py:class:`dict`
    """

    fileobject = _open_anything(jsonfile)
    config = json.load(fileobject)

    return config


def config_to_json(config, tofile=None):
    """
    Export the setting in a ConfigHandler instance to JSON format.
    Optionally write the JSON construct to file

    :param config: configuration to export
    :type config:  :lie_config:ConfigHandler
    :param tofile: filepath to write exported JSON to
    :type tofile:  str
    """

    nested_dict = _nest_flattened_dict(config())
    jsonconfig = json.dumps(nested_dict, indent=4, sort_keys=True)

    if tofile:
        with open(tofile, 'w') as cf:
            cf.write(jsonconfig)
    else:
        return jsonconfig


def config_from_yaml(yamlfile):
    """
    Import configuration from a YAML file or string

    :param yamlfile: configuration to be parsed
    :type yamlfile:  any type accepted by _open_anything function

    :return:        parsed configuration
    :rtype:         :py:class:`dict`
    """

    from yaml import load
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    fileobject = _open_anything(yamlfile)
    config = load(fileobject, Loader=Loader)

    return config


def config_to_yaml(config, tofile=None, **kwargs):
    """
    Export the setting in a ConfigHandler instance to YAML format.
    Optionally write the YAML construct to file

    :param config: configuration to export
    :type config:  :lie_config:ConfigHandler
    :param tofile: filepath to write exported YAML to
    :type tofile:  str
    :param kwargs: optional keyword arguments to the pyyaml dump function
    """

    from yaml import dump
    try:
        from yaml import CDumper as Dumper
    except ImportError:
        from yaml import Dumper

    nested_dict = _nest_flattened_dict(config())
    yamlconfig = dump(nested_dict, Dumper=Dumper, **kwargs)

    if tofile:
        with open(tofile, 'w') as cf:
            cf.write(yamlconfig)
    else:
        return yamlconfig

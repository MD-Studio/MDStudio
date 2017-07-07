# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import time
import json

from autobahn import wamp
from twisted.internet.defer import inlineCallbacks

from lie_componentbase import BaseApplicationSession
from lie_componentbase.config import config_to_json


class ConfigWampApi(BaseApplicationSession):
    """
    Configuration management WAMP methods.
    """

    @wamp.register(u'liestudio.config.get')
    def getConfig(self, key, config='default'):
        """
        Retrieve application configuration.

        Search for `key` anywhere in a globally accessible configuration store.
        Returns query results in JSON format.
        `key` may be a single string to search for or a list of strings in
        wich case the resulting configuration dictionary is the collection of
        individual query results

        :param key:    configuration key to search for
        :type key:     string or list of strings
        :param config: configuration store to look in (`default`)
        :type config:  string

        :rtype:        :py:class:`dict`
        """

        if not isinstance(key, (tuple, list)):
            key = [key]
        key = ['*{0}*'.format(str(k)) for k in key]

        settings = self.package_config.search(key)
        return settings.dict(nested=True)

    def onExit(self, details):
        """
        Config component exit routine

        Save the updated global configuration back to the settings.json file

        :param settings: global and module specific settings
        :type settings:  :py:class:`dict` or :py:class:`dict` like object
        """

        app_config = self.package_config.get('system.app_config')
        if app_config and os.path.isfile(app_config):
            config_to_json(self.package_config, app_config)


def make(config):
    """
    Component factory

    This component factory creates instances of the application component
    to run.

    The function will get called either during development using an
    ApplicationRunner, or as a plugin hosted in a WAMPlet container such as
    a Crossbar.io worker.
    The BaseApplicationSession class is initiated with an instance of the
    ComponentConfig class by default but any class specific keyword arguments
    can be consument as well to populate the class session_config and
    package_config dictionaries.

    :param config: Autobahn ComponentConfig object
    """

    if config:
        return ConfigWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio configuration management WAMPlet',
                'description': 'WAMPlet proving LIEStudio configuration management endpoints'}

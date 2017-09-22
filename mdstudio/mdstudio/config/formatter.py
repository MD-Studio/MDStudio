# coding=utf-8

from string import Formatter

# import the placeholder if needed
from mdstudio.config.io import *


class ConfigFormatter(Formatter):

    def __init__(self, config):

        self.config = config

    def get_value(self, key, args=None, kwargs=None):

        # Only work on string based placeholders
        # string or unicode for python2.x, str == unicode for python 3.x
        if isinstance(key, (str, unicode)):
            return self.config[key]

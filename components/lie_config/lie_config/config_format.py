#!/usr/bin/env python

from string import Formatter


class ConfigFormatter(Formatter):

    def __init__(self, config):

        self.config = config

    def get_value(self, key, args, kwargs):

        # Only work on string based placeholders
        # string or unicode for python2.x, str == unicode for python 3.x
        if isinstance(key, (str, unicode)):
            return self.config[key]

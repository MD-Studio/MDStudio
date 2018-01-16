# -*- coding: utf-8 -*-

"""
file: decorator_test.py

Unit tests for the lie_config component
"""

from lie_config import configwrapper, get_config


@configwrapper()
def decorator_method_defined(value, lv=1, gv=2):
    """
    configwrapper decorated function that has keyword
    arguments defined in the global configuration.

    the keyword arguments to the function are dynamically
    overloaded with settings from the global configuration.
    """

    return value * lv, value * gv


@configwrapper()
def decorator_method_undefined(value, lv=1, gv=2):
    """
    configwrapper decorated function that does not
    have it's keyword arguments defined in the global
    configuration. Keyword arguments will not be overladed.
    """

    return value * lv, value * gv


@configwrapper()
def decorator_method_withkwargs(value, lv=1, gv=2, **kwargs):
    """
    configwrapper decorated function that has keyword
    arguments defined in the global configuration.

    the keyword arguments to the function are dynamically
    overloaded with settings from the global configuration.
    """

    return value * lv, value * gv, kwargs


@configwrapper(['decorator_method_withkwargs', 'system'])
def decorator_method_resolutionorder(value, lv=1, gv=2):
    """
    configwrapper decorated function that has keyword
    arguments defined in the global configuration.

    the keyword arguments to the function are dynamically
    overloaded with settings from the global configuration.
    """

    return value * lv, value * gv


def change_value_elsewhere(key, value):
    """
    Emulate a change to the global configuration from
    elsewhere in the Python runtime.
    """

    settings = get_config()
    settings[key] = value


@configwrapper()
class DecoratorClass(object):
    """
    configwrapper decorated class that has keyword
    arguments defined in the global configuration.
    """

    def __init__(self, lv=1, gv=2):

        self.lv = lv
        self.gv = gv

    def run(self, value):

        return value * self.lv, value * self.gv

    @configwrapper()
    def decorated_run(self, value, mod=1):

        return (value * self.lv * mod), (value * self.gv * mod)

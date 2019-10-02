# -*- coding: utf-8 -*-

from mock import patch


def load_settings(cls, settings):
    return patch.object(cls, '_retrieve_stored_settings', return_value=settings)

# -*- coding: utf-8 -*-
import unittest

import os

from mdstudio.config import ConfigHandler
from mdstudio.config.io import config_from_json
from mdstudio.config.orm_handler import ConfigOrmHandler


class _taskMeta(object):

    def custommethod(self):

        return "custom method"


class ConfigHandlerORMTests(unittest.TestCase):
    """
    Unittest ConfigHandler ORM tests
    """

    _currpath = os.path.abspath(__file__)
    _settings_json = os.path.join(os.path.dirname(_currpath), 'files/orm_test.json')

    def setUp(self):
        """
        ConfigHandlerTests class setup

        Load test settings file from orm_test.json
        """

        data = config_from_json(self._settings_json)

        # Setup ORM handler
        orm = ConfigOrmHandler(ConfigHandler)
        orm.add('_taskMeta', _taskMeta)

        self.settings = ConfigHandler(orm=orm)
        self.settings.load(data)

    def test_orm_mapper(self):

        b = self.settings._taskMeta
        self.assertTrue(hasattr(b, 'custommethod'))
        self.assertEqual(b.custommethod(), "custom method")

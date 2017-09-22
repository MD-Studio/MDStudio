# -*- coding: utf-8 -*-
import unittest

from mdstudio.config.formatter import ConfigFormatter


class ConfigFormatterTests(unittest.TestCase):
    def test_string_key(self):
        obj = ConfigFormatter({'test': 2})

        self.assertEqual(obj.get_value('test'), 2)

    def test_int_key(self):
        obj = ConfigFormatter({3: 2})

        self.assertEqual(obj.get_value(3), None)
        self.assertEqual(obj.get_value(2), None)

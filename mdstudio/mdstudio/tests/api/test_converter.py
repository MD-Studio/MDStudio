import datetime
from unittest import TestCase

import pytz

from mdstudio.api.converter import convert_obj_to_json


class ConverterTest(TestCase):

    def test_convert_obj_to_json_date_time(self):
        document = {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'f': '2017-10-26T09:15:00+00:00'
        }
        convert_obj_to_json(document)
        self.assertEqual(document, {
            'date': '2017-10-26T09:16:00+00:00',
            'f': '2017-10-26T09:15:00+00:00'
        })

    def test_convert_obj_to_json_date_time_nested(self):
        document = {
            'o': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                'f': '2017-10-26T09:15:00+00:00'
            }
        }
        convert_obj_to_json(document)
        self.assertEqual(document, {
            'o': {
                'date': '2017-10-26T09:16:00+00:00',
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_convert_obj_to_json_date_time_nested_list(self):
        document = {
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                         datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        }
        convert_obj_to_json(document)
        self.assertEqual(document, {
            'o': {
                'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00'],
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_convert_obj_to_json_date(self):
        document = {
            'date': datetime.date(2017, 10, 26),
            'f': '2017-10-26'
        }
        convert_obj_to_json(document)
        self.assertEqual(document, {
            'date': '2017-10-26',
            'f': '2017-10-26'
        })

    def test_convert_obj_to_json_date_nested(self):
        document = {
            'o': {
                'date': datetime.date(2017, 10, 26),
                'f': '2017-10-26'
            }
        }
        convert_obj_to_json(document)
        self.assertEqual(document, {
            'o': {
                'date': '2017-10-26',
                'f': '2017-10-26'
            }
        })

    def test_convert_obj_to_json_date_nested_list(self):
        document = {
            'o': {
                'date': [datetime.date(2017, 10, 26),
                         datetime.date(2017, 10, 26)],
                'f': '2017-10-26'
            }
        }
        convert_obj_to_json(document)
        self.assertEqual(document, {
            'o': {
                'date': ['2017-10-26', '2017-10-26'],
                'f': '2017-10-26'
            }
        })

    def test_convert_obj_to_json_date_time_mixed(self):
        document = {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'date2': datetime.date(2017, 10, 26)
        }
        convert_obj_to_json(document)
        self.assertEqual(document, {
            'date': '2017-10-26T09:16:00+00:00',
            'date2': '2017-10-26'
        })

    def test_convert_obj_to_json_date_time_mixed2(self):
        document = {
            'date2': datetime.date(2017, 10, 26),
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
        }
        convert_obj_to_json(document)
        self.assertEqual(document, {
            'date2': '2017-10-26',
            'date': '2017-10-26T09:16:00+00:00'
        })

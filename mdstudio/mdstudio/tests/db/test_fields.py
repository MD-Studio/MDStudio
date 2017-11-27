# coding=utf-8
import datetime

import binascii
import pytz
from copy import deepcopy
from cryptography.fernet import Fernet
from mock import mock
from unittest2 import TestCase

from mdstudio.db.database import Fields
from mdstudio.db.exception import DatabaseException
from mdstudio.utc import now


class FieldsTests(TestCase):

    def test_convert_call_date_time(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        f = Fields(date_times=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
        })

    def test_convert_call_date_time_nested(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'o': {
                'date2': '2017-9-26T09:16:00+00:00'
            }
        }
        f = Fields(date_times=['date', 'o.date2'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'o': {
                'date2': datetime.datetime(2017, 9, 26, 9, 16, tzinfo=pytz.utc)
            }
        })

    def test_convert_call_date_time_overnested(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'o': {
                'date2': '2017-9-26T09:16:00+00:00'
            }
        }
        f = Fields(date_times=['o.o.date2'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': '2017-10-26T09:16:00+00:00',
            'o': {
                'date2': '2017-9-26T09:16:00+00:00'
            }
        })

    def test_convert_call_date_time_no_conversion(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'f': '2017-10-26T09:15:00+00:00'
        }
        f = Fields(date_times=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'f': '2017-10-26T09:15:00+00:00'
        })

    def test_convert_call_date_time_list(self):
        document = {
            'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00']
        }
        f = Fields(date_times=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                     datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)]
        })

    def test_convert_call_date_time_no_list(self):
        document = {
            'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00']
        }
        f = Fields(date_times=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                     datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)]
        })

    def test_convert_call_date_time_object_list(self):
        document = {
            'dates': [
                {
                    'date': '2017-10-26T09:16:00+00:00'
                },
                {
                    'date': '2017-10-26T09:15:00+00:00'
                }
            ]
        }
        f = Fields(date_times=['dates.date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'dates': [
                {
                    'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
                },
                {
                    'date': datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)
                }
            ]
        })

    def test_convert_call_date_time_object_list2(self):
        document = {
            'dates': [
                {
                    'date': {
                        'o': '2017-10-26T09:16:00+00:00'
                    }
                },
                {
                    'date': {
                        'o': '2017-10-26T09:15:00+00:00'
                    }
                }
            ]
        }
        f = Fields(date_times=['dates.date.o'])
        f.convert_call(document)
        self.assertEqual(document, {
            'dates': [
                {
                    'date': {
                        'o': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
                    }
                },
                {
                    'date': {
                        'o': datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)
                    }
                }
            ]
        })

    def test_convert_call_date_time_object_list_nonexisting(self):
        document = {
            'dates': [
                {
                    'date': '2017-10-26T09:16:00+00:00'
                },
                {
                    'date2': '2017-10-26T09:15:00+00:00'
                }
            ]
        }
        f = Fields(date_times=['dates.date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'dates': [
                {
                    'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
                },
                {
                    'date2': '2017-10-26T09:15:00+00:00'
                }
            ]
        })

    def test_convert_call_date_time_none(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'f': '2017-10-26T09:15:00+00:00'
        }
        cdocument = deepcopy(document)
        f = Fields()
        f.convert_call(cdocument)
        self.assertEqual(cdocument, document)

    def test_convert_call_date_time_other(self):
        document = {
            'date': 200,
            'f': '2017-10-26T09:15:00+00:00'
        }
        cdocument = deepcopy(document)
        self.assertRaisesRegex(DatabaseException, "Failed to parse datetime field '200'", lambda: Fields(date_times=['date']).convert_call(cdocument))

    def test_convert_call_date_time_nonexisting_key(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        cdocument = deepcopy(document)
        f = Fields(date_times=['date2'])
        f.convert_call(cdocument)
        self.assertEqual(cdocument, document)

    def test_convert_call_date_time_prefixes_none(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        cdocument = deepcopy(document)
        f = Fields(date_times=['date'])
        f.convert_call(cdocument, ['insert'])
        self.assertEqual(cdocument, document)

    def test_convert_call_date_time_prefixes(self):
        document = {
            'insert': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        }
        f = Fields(date_times=['date'])
        f.convert_call(document, ['insert'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
            }
        })

    def test_convert_call_date_time_prefixes2(self):
        document = {
            'insert': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'inserts': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'insert2': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        }
        f = Fields(date_times=['date'])
        f.convert_call(document, ['insert', 'inserts'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
            },
            'inserts': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
            },
            'insert2': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        })

    def test_convert_call_date_time_prefixes_existing(self):
        document = {
            'insert': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'inserts': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'insert2': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        }
        f = Fields(date_times=['insert.date'])
        f.convert_call(document, ['insert', 'inserts'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
            },
            'inserts': {
                'date': '2017-10-26T09:16:00+00:00'
            },
            'insert2': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        })

    def test_convert_call_date_time_prefixes_operators(self):
        document = {
            'insert': {
                '$insert': {
                    'date': '2017-10-26T09:16:00+00:00'
                },
                '$inserts': {
                    'date': '2017-9-26T09:16:00+00:00'
                },
                '$insert2': {
                    'date': '2017-8-26T09:16:00+00:00'
                }
            }
        }
        f = Fields(date_times=['date'])
        f.convert_call(document, ['insert'])
        self.assertEqual(document, {
            'insert': {
                '$insert': {
                    'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
                },
                '$inserts': {
                    'date': datetime.datetime(2017, 9, 26, 9, 16, tzinfo=pytz.utc)
                },
                '$insert2': {
                    'date': datetime.datetime(2017, 8, 26, 9, 16, tzinfo=pytz.utc)
                }
            }
        })

    def test_convert_call_date(self):
        document = {
            'date': '2017-10-26'
        }
        f = Fields(dates=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': datetime.date(2017, 10, 26)
        })

    def test_convert_call_date_date_time(self):
        document = {
            'date':  datetime.datetime(2017, 10, 26)
        }
        f = Fields(dates=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': datetime.date(2017, 10, 26)
        })

    def test_convert_call_date_date(self):
        document = {
            'date':  datetime.date(2017, 10, 26)
        }
        f = Fields(dates=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': datetime.date(2017, 10, 26)
        })

    def test_convert_call_date_nested(self):
        document = {
            'date': '2017-10-26',
            'o': {
                'date2': '2017-9-26'
            }
        }
        f = Fields(dates=['date', 'o.date2'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': datetime.date(2017, 10, 26),
            'o': {
                'date2': datetime.date(2017, 9, 26)
            }
        })

    def test_convert_call_date_overnested(self):
        document = {
            'date': '2017-10-26',
            'o': {
                'date2': '2017-9-26'
            }
        }
        f = Fields(dates=['o.o.date2'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': '2017-10-26',
            'o': {
                'date2': '2017-9-26'
            }
        })

    def test_convert_call_date_no_conversion(self):
        document = {
            'date': '2017-10-26',
            'f': '2017-10-26'
        }
        f = Fields(dates=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': datetime.date(2017, 10, 26),
            'f': '2017-10-26'
        })

    def test_convert_call_date_list(self):
        document = {
            'date': ['2017-10-26', '2017-10-26']
        }
        f = Fields(dates=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': [datetime.date(2017, 10, 26),
                     datetime.date(2017, 10, 26)]
        })

    def test_convert_call_date_no_list(self):
        document = {
            'date': ['2017-10-26', '2017-10-26']
        }
        f = Fields(dates=['date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'date': [datetime.date(2017, 10, 26),
                     datetime.date(2017, 10, 26)]
        })

    def test_convert_call_date_object_list(self):
        document = {
            'dates': [
                {
                    'date': '2017-10-26'
                },
                {
                    'date': '2017-10-26'
                }
            ]
        }
        f = Fields(dates=['dates.date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'dates': [
                {
                    'date': datetime.date(2017, 10, 26)
                },
                {
                    'date': datetime.date(2017, 10, 26)
                }
            ]
        })

    def test_convert_call_date_object_list2(self):
        document = {
            'dates': [
                {
                    'date': {
                        'o': '2017-10-26'
                    }
                },
                {
                    'date': {
                        'o': '2017-10-26'
                    }
                }
            ]
        }
        f = Fields(dates=['dates.date.o'])
        f.convert_call(document)
        self.assertEqual(document, {
            'dates': [
                {
                    'date': {
                        'o': datetime.date(2017, 10, 26)
                    }
                },
                {
                    'date': {
                        'o': datetime.date(2017, 10, 26)
                    }
                }
            ]
        })

    def test_convert_call_date_object_list_nonexisting(self):
        document = {
            'dates': [
                {
                    'date': '2017-10-26'
                },
                {
                    'date2': '2017-10-26'
                }
            ]
        }
        f = Fields(dates=['dates.date'])
        f.convert_call(document)
        self.assertEqual(document, {
            'dates': [
                {
                    'date': datetime.date(2017, 10, 26)
                },
                {
                    'date2': '2017-10-26'
                }
            ]
        })

    def test_convert_call_date_none(self):
        document = {
            'date': '2017-10-26',
            'f': '2017-10-26'
        }
        cdocument = deepcopy(document)
        f = Fields()
        f.convert_call(cdocument)
        self.assertEqual(cdocument, document)

    def test_convert_call_date_other(self):
        document = {
            'date': 200,
            'f': '2017-10-26'
        }
        cdocument = deepcopy(document)
        self.assertRaisesRegex(DatabaseException, "Failed to parse date field '200'", lambda: Fields(dates=['date']).convert_call(cdocument))

    def test_convert_call_date_nonexisting_key(self):
        document = {
            'date': '2017-10-26'
        }
        cdocument = deepcopy(document)
        f = Fields(dates=['date2'])
        f.convert_call(cdocument)
        self.assertEqual(cdocument, document)

    def test_convert_call_date_prefixes_none(self):
        document = {
            'date': '2017-10-26'
        }
        cdocument = deepcopy(document)
        f = Fields(dates=['date'])
        f.convert_call(cdocument, ['insert'])
        self.assertEqual(cdocument, document)

    def test_convert_call_date_prefixes(self):
        document = {
            'insert': {
                'date': '2017-10-26'
            }
        }
        f = Fields(dates=['date'])
        f.convert_call(document, ['insert'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.date(2017, 10, 26)
            }
        })

    def test_convert_call_date_prefixes2(self):
        document = {
            'insert': {
                'date': '2017-10-26'
            },
            'inserts': {
                'date': '2017-10-26'
            },
            'insert2': {
                'date': '2017-10-26'
            }
        }
        f = Fields(dates=['date'])
        f.convert_call(document, ['insert', 'inserts'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.date(2017, 10, 26)
            },
            'inserts': {
                'date': datetime.date(2017, 10, 26)
            },
            'insert2': {
                'date': '2017-10-26'
            }
        })

    def test_convert_call_date_prefixes_existing(self):
        document = {
            'insert': {
                'date': '2017-10-26'
            },
            'inserts': {
                'date': '2017-10-26'
            },
            'insert2': {
                'date': '2017-10-26'
            }
        }
        f = Fields(dates=['insert.date'])
        f.convert_call(document, ['insert', 'inserts'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.date(2017, 10, 26)
            },
            'inserts': {
                'date': '2017-10-26'
            },
            'insert2': {
                'date': '2017-10-26'
            }
        })

    def test_convert_call_date_prefixes_operators(self):
        document = {
            'insert': {
                '$insert': {
                    'date': '2017-10-26'
                },
                '$inserts': {
                    'date': '2017-9-26'
                },
                '$insert2': {
                    'date': '2017-8-26'
                }
            }
        }
        f = Fields(dates=['date'])
        f.convert_call(document, ['insert'])
        self.assertEqual(document, {
            'insert': {
                '$insert': {
                    'date': datetime.date(2017, 10, 26)
                },
                '$inserts': {
                    'date': datetime.date(2017, 9, 26)
                },
                '$insert2': {
                    'date': datetime.date(2017, 8, 26)
                }
            }
        })

    def test_datetime_conversion(self):
        tz = pytz.timezone('Pacific/Johnston')

        now_tz = datetime.datetime.now(tz)
        doc = {'createdAt': now_tz}
        f = Fields(date_times=['createdAt'])
        f.convert_call(doc)

        self.assertEqual(doc['createdAt'], now_tz)
        self.assertLess(now() - doc['createdAt'], datetime.timedelta(seconds=1))

    def test_datetime_without_tzinfo(self):
        now_tzless = datetime.datetime.now()
        doc = {'createdAt': now_tzless}

        f = Fields(date_times=['createdAt'])
        self.assertRaises(DatabaseException, lambda: f.convert_call(doc))

    def test_uses_encryption(self):
        self.assertFalse(Fields().uses_encryption)
        self.assertFalse(Fields(dates=['test']).uses_encryption)
        self.assertFalse(Fields(date_times=['test']).uses_encryption)
        self.assertTrue(Fields(encrypted=['test']).uses_encryption)

    def test_encryption_fields(self):
        self.field = Fields(encrypted=['test'])
        self.field._key_repository = mock.MagicMock()
        self.field._key_repository.get_key = mock.MagicMock(return_value=Fernet.generate_key())
        obj = {
            'test': 'hello world'
        }
        obj2 = deepcopy(obj)
        self.field.convert_call(obj2, None, {'username': 'user'})

        self.field._key_repository.get_key.assert_called_once_with({'username': 'user'})

        self.assertNotEqual(obj, obj2)
        self.assertRegex(obj2['test'], '__encrypted__:')
        self.field.parse_result(obj2, {'username': 'user'})
        self.assertEqual(obj, obj2)

        obj3 = deepcopy(obj)
        self.field.convert_call(obj3, None, {'username': 'user'})
        self.assertNotEqual(obj3, obj2)

    def test_encryption_fields_none(self):
        self.field = Fields(encrypted=['test'])
        self.field._key_repository = mock.MagicMock()
        self.field._key_repository.get_key = mock.MagicMock(return_value=Fernet.generate_key())
        obj = {
            'test': 'hello world'
        }
        obj2 = deepcopy(obj)
        self.field.convert_call(obj2, None)

        self.assertEqual(obj, obj2)

    def test_encryption_fields_none2(self):
        self.field = Fields(encrypted=['test'])
        self.field._key_repository = mock.MagicMock()
        self.field._key_repository.get_key = mock.MagicMock(return_value=Fernet.generate_key())
        obj = {
            'test': 'hello world'
        }
        obj2 = deepcopy(obj)
        self.field.convert_call(obj2, None, {'username': 'user'})

        self.assertNotEqual(obj, obj2)
        self.assertRegex(obj2['test'], '__encrypted__:')
        self.field.parse_result(obj2)
        self.assertRegex(obj2['test'], '__encrypted__:')
        self.assertNotEqual(obj, obj2)

    def test_encryption_fields_bytes(self):
        self.field = Fields(encrypted=['test'])
        self.field._key_repository = mock.MagicMock()
        self.field._key_repository.get_key = mock.MagicMock(return_value=Fernet.generate_key())
        obj = {
            'test': b'hello world'
        }
        obj2 = deepcopy(obj)
        self.field.convert_call(obj2, None, {'username': 'user'})

        self.assertNotEqual(obj, obj2)
        self.assertRegex(obj2['test'], '__encrypted__:')
        self.field.parse_result(obj2, {'username': 'user'})
        self.assertEqual(obj['test'].decode('utf-8'), obj2['test'])

    def test_encryption_fields_int(self):
        self.field = Fields(encrypted=['test'])
        self.field._key_repository = mock.MagicMock()
        self.field._key_repository.get_key = mock.MagicMock(return_value=Fernet.generate_key())
        obj = {
            'test': 2
        }
        obj2 = deepcopy(obj)
        self.assertRaisesRegex(DatabaseException, "Failed to encrypt field '2'", self.field.convert_call, obj2, None, {'username': 'user'})

    def test_encryption_fields_wrong_key(self):
        self.field = Fields(encrypted=['test'])
        self.field._key_repository = mock.MagicMock()
        self.field._key_repository.get_key = mock.MagicMock(return_value=b'123456')
        obj = {
            'test': 'hello world'
        }
        obj2 = deepcopy(obj)
        self.assertRaisesRegex(DatabaseException, "Failed to create a Fernet encryption class due to an incorrect key.",
                               self.field.convert_call, obj2, None, {'username': 'user'})


    def test_encryption_fields_decrypt_wrong_key(self):
        self.field = Fields(encrypted=['test'])
        self.field._key_repository = mock.MagicMock()
        self.field._key_repository.get_key = mock.MagicMock(return_value=b'123456')
        self.field._logger = mock.MagicMock()
        obj = {
            'test': 'hello world'
        }
        obj2 = deepcopy(obj)
        self.assertRaisesRegex(DatabaseException, "Failed to create a Fernet encryption class due to an incorrect key.",
                               self.field.parse_result, obj2, {'username': 'user'})

    def test_encryption_fields_decrypt_fails(self):
        self.field = Fields(encrypted=['test'])
        self.field._key_repository = mock.MagicMock()
        self.field._key_repository.get_key = mock.MagicMock(return_value=Fernet.generate_key())
        obj = {
            'test': 'hello world'
        }
        obj2 = deepcopy(obj)
        self.assertRaises(DatabaseException, self.field.parse_result, obj2, {'username': 'user'})
        self.assertEqual(obj, obj2)

    def test_to_dict(self):
        fields = Fields(date_times=['test'], dates=['test2'], encrypted=['test3'])
        self.assertEqual(fields.to_dict(), {
            'date': ['test2'],
            'datetime': ['test'],
            'encrypted': ['test3']
        })

    def test_to_dict2(self):
        fields = Fields(date_times=['test'])
        self.assertEqual(fields.to_dict(), {
            'datetime': ['test']
        })

    def test_to_dict3(self):
        fields = Fields(dates=['test2'])
        self.assertEqual(fields.to_dict(), {
            'date': ['test2']
        })

    def test_to_dict4(self):
        fields = Fields(encrypted=['test3'])
        self.assertEqual(fields.to_dict(), {
            'encrypted': ['test3']
        })

    def test_from_dict(self):
        self.assertEqual(Fields.from_dict({
            'date': ['test2'],
            'datetime': ['test'],
            'encrypted': ['test3']
        }), Fields(date_times=['test'], dates=['test2'], encrypted=['test3']))

    def test_from_dict2(self):
        self.assertEqual(Fields.from_dict({
        }), Fields())


    def test_from_dict3(self):
        self.assertEqual(Fields.from_dict({
            'date': 'test2',
            'datetime': 'test',
            'encrypted': 'test3'
        }), Fields(date_times=['test'], dates=['test2'], encrypted=['test3']))
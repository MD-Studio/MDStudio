# coding=utf-8
import datetime

import pytz
from copy import deepcopy

import mock
from twisted.trial.unittest import TestCase

from mdstudio.db.database import IDatabase
from mdstudio.db.exception import DatabaseException
from mdstudio.deferred.chainable import chainable
from mdstudio.utc import now


class DatabaseTests(TestCase):
    @mock.patch.multiple(IDatabase, __abstractmethods__=set())
    @chainable
    def test_transform(self):
        db = IDatabase()
        identity = lambda x: x
        const = lambda x: 2
        self.assertEqual((yield db.transform(None, identity)), None)
        self.assertEqual((yield db.transform(None, const)), None)
        self.assertEqual((yield db.transform(4, const)), 2)
        self.assertEqual((yield db.transform(3, identity)), 3)
        self.assertEqual((yield db.transform(2, lambda x: x ** 2)), 4)
        self.assertEqual((yield db.transform('test', identity)), 'test')

    @mock.patch.multiple(IDatabase, __abstractmethods__=set())
    def test_extract(self):
        db = IDatabase()
        d = {
            'test': 2,
            'test2': 3
        }
        self.assertEqual(db.extract(d, 'test'), 2)
        self.assertEqual(db.extract(d, 'test2'), 3)


    def test_transform_to_datetime(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        IDatabase.transform_to_datetime(document, ['date'])
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
        })

    def test_transform_to_datetime_nested(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'o': {
                'date2': '2017-9-26T09:16:00+00:00'
            }
        }
        IDatabase.transform_to_datetime(document, ['date', 'o.date2'])
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'o': {
                'date2': datetime.datetime(2017, 9, 26, 9, 16, tzinfo=pytz.utc)
            }
        })

    def test_transform_to_datetime_overnested(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'o': {
                'date2': '2017-9-26T09:16:00+00:00'
            }
        }
        IDatabase.transform_to_datetime(document, ['o.o.date2'])
        self.assertEqual(document, {
            'date': '2017-10-26T09:16:00+00:00',
            'o': {
                'date2': '2017-9-26T09:16:00+00:00'
            }
        })

    def test_transform_to_datetime_no_conversion(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'f': '2017-10-26T09:15:00+00:00'
        }
        IDatabase.transform_to_datetime(document, ['date'])
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'f': '2017-10-26T09:15:00+00:00'
        })

    def test_transform_to_datetime_list(self):
        document = {
            'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00']
        }
        IDatabase.transform_to_datetime(document, ['date'])
        self.assertEqual(document, {
            'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                     datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)]
        })

    def test_transform_to_datetime_no_list(self):
        document = {
            'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00']
        }
        IDatabase.transform_to_datetime(document, 'date')
        self.assertEqual(document, {
            'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                     datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)]
        })

    def test_transform_to_datetime_object_list(self):
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
        IDatabase.transform_to_datetime(document, ['dates.date'])
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

    def test_transform_to_datetime_object_list2(self):
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
        IDatabase.transform_to_datetime(document, ['dates.date.o'])
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

    def test_transform_to_datetime_object_list_nonexisting(self):
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
        IDatabase.transform_to_datetime(document, ['dates.date'])
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

    def test_transform_to_datetime_none(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00',
            'f': '2017-10-26T09:15:00+00:00'
        }
        cdocument = deepcopy(document)
        IDatabase.transform_to_datetime(cdocument, None)
        self.assertEqual(cdocument, document)

    def test_transform_to_datetime_other(self):
        document = {
            'date': 200,
            'f': '2017-10-26T09:15:00+00:00'
        }
        cdocument = deepcopy(document)
        self.assertRaisesRegex(DatabaseException, "Failed to parse datetime field '200'", IDatabase.transform_to_datetime, cdocument, 'date')

    def test_transform_to_datetime_nonexisting_key(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        cdocument = deepcopy(document)
        IDatabase.transform_to_datetime(cdocument, ['date2'])
        self.assertEqual(cdocument, document)

    def test_transform_to_datetime_prefixes_none(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        cdocument = deepcopy(document)
        IDatabase.transform_to_datetime(cdocument, ['date'], ['insert'])
        self.assertEqual(cdocument, document)

    def test_transform_to_datetime_prefixes(self):
        document = {
            'insert': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        }
        IDatabase.transform_to_datetime(document, ['date'], ['insert'])
        self.assertEqual(document, {
            'insert': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc)
            }
        })

    def test_transform_to_datetime_prefixes2(self):
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
        IDatabase.transform_to_datetime(document, ['date'], ['insert', 'inserts'])
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

    def test_transform_to_datetime_prefixes_existing(self):
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
        IDatabase.transform_to_datetime(document, ['insert.date'], ['insert', 'inserts'])
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

    def test_datetime_conversion(self):
        tz = pytz.timezone('Pacific/Johnston')

        now_tz = datetime.datetime.now(tz)
        doc = {'createdAt': now_tz}
        IDatabase.transform_to_datetime(doc, ['createdAt'])

        self.assertEqual(doc['createdAt'], now_tz)
        self.assertLess(now() - doc['createdAt'], datetime.timedelta(seconds=1))

    def test_datetime_without_tzinfo(self):
        now_tzless = datetime.datetime.now()
        doc = {'createdAt': now_tzless}

        self.assertRaises(DatabaseException, lambda: IDatabase.transform_to_datetime(doc, ['createdAt']))

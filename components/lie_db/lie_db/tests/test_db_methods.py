# coding=utf-8
import time

import datetime

import pytz
import twisted
from bson import ObjectId
from copy import deepcopy
from mock import mock
from twisted.internet import reactor

from lie_db.db_methods import MongoDatabaseWrapper
from lie_db.mongo_client_wrapper import MongoClientWrapper
from mdstudio.db.model import Model
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.unittest.mongo import TrialDBTestCase

twisted.internet.base.DelayedCall.debug = True

class TestMongoDatabaseWrapper(TrialDBTestCase):
    def setUp(self):
        self.db = MongoClientWrapper("localhost", 27127).get_namespace('testns')
        self.d = Model(self.db, 'test_collection')

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()


    def test_transform_to_datetime(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        self.db._transform_to_datetime(document, ['date'])
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
        self.db._transform_to_datetime(document, ['date', 'o.date2'])
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
        self.db._transform_to_datetime(document, ['o.o.date2'])
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
        self.db._transform_to_datetime(document, ['date'])
        self.assertEqual(document, {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'f': '2017-10-26T09:15:00+00:00'
        })

    def test_transform_to_datetime_list(self):
        document = {
            'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00']
        }
        self.db._transform_to_datetime(document, ['date'])
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
        self.db._transform_to_datetime(document, ['dates.date'])
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
        self.db._transform_to_datetime(document, ['dates.date.o'])
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
        self.db._transform_to_datetime(document, ['dates.date'])
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
        self.db._transform_to_datetime(cdocument, None)
        self.assertEqual(cdocument, document)

    def test_transform_to_datetime_nonexisting_key(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        cdocument = deepcopy(document)
        self.db._transform_to_datetime(cdocument, ['date2'])
        self.assertEqual(cdocument, document)

    def test_transform_to_datetime_prefixes_none(self):
        document = {
            'date': '2017-10-26T09:16:00+00:00'
        }
        cdocument = deepcopy(document)
        self.db._transform_to_datetime(cdocument, ['date'], ['insert'])
        self.assertEqual(cdocument, document)

    def test_transform_to_datetime_prefixes(self):
        document = {
            'insert': {
                'date': '2017-10-26T09:16:00+00:00'
            }
        }
        self.db._transform_to_datetime(document, ['date'], ['insert'])
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
        self.db._transform_to_datetime(document, ['date'], ['insert', 'inserts'])
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
        self.db._transform_to_datetime(document, ['insert.date'], ['insert', 'inserts'])
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

    def test_transform_datetime_to_isostring(self):
        document = {
            'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
            'f': '2017-10-26T09:15:00+00:00'
        }
        self.db._transform_datetime_to_isostring(document)
        self.assertEqual(document, {
            'date': '2017-10-26T09:16:00+00:00',
            'f': '2017-10-26T09:15:00+00:00'
        })


    def test_transform_datetime_to_isostring_nested(self):
        document = {
            'o': {
                'date': datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc),
                'f': '2017-10-26T09:15:00+00:00'
            }
        }
        self.db._transform_datetime_to_isostring(document)
        self.assertEqual(document, {
            'o': {
                'date': '2017-10-26T09:16:00+00:00',
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_transform_datetime_to_isostring_nested_list(self):
        document = {
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc), datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        }
        self.db._transform_datetime_to_isostring(document)
        self.assertEqual(document, {
            'o': {
                'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00'],
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_json(self):
        document = {
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc), datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        self.db._prepare_for_json(document)

        self.assertEqual(document, {
            'o': {
                'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00'],
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_json_id(self):
        document = {
            '_id': 1000,
            'o': {
                'date': [datetime.datetime(2017, 10, 26, 9, 16, tzinfo=pytz.utc), datetime.datetime(2017, 10, 26, 9, 15, tzinfo=pytz.utc)],
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        self.db._prepare_for_json(document)

        self.assertEqual(document, {
            '_id': '1000',
            'o': {
                'date': ['2017-10-26T09:16:00+00:00', '2017-10-26T09:15:00+00:00'],
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_json_none(self):
        document = None

        self.db._prepare_for_json(document)

        self.assertEqual(document, None)

    def test_prepare_for_mongo(self):
        document = {
            'o': {
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        self.db._prepare_for_mongo(document)

        self.assertEqual(document, {
            'o': {
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_mongo_id(self):
        document = {
            '_id': '0123456789ab0123456789ab',
            'o': {
                'f': '2017-10-26T09:15:00+00:00'
            }
        }

        self.db._prepare_for_mongo(document)

        self.assertEqual(document, {
            '_id': ObjectId('0123456789ab0123456789ab'),
            'o': {
                'f': '2017-10-26T09:15:00+00:00'
            }
        })

    def test_prepare_for_mongo_none(self):
        document = None

        self.db._prepare_for_mongo(document)

        self.assertEqual(document, None)

    @chainable
    def _test_insert_one(self):

        id = yield self.d.insert_one({'test': 2, '_id': 80})
        self.assertEqual(id, '80')

        found = yield self.d.find_one({'_id': 80})

        self.assertEqual(found, {'test': 2, '_id': '80'})
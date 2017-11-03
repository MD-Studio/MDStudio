import os
from autobahn.wamp import PublishOptions
from mock import mock
from mongomock import ObjectId
from twisted.internet import reactor

from lie_db import DBWampApi
from lie_db.db_methods import MongoDatabaseWrapper
from mdstudio.deferred.chainable import chainable
from mdstudio.unittest import wait_for_completion
from mdstudio.unittest.api import APITestCase
from mdstudio.unittest.db import DBTestCase
from mdstudio.util import WampSchema
from faker import Faker


class TestWampService(DBTestCase, APITestCase):
    def setUp(self):
        self.service = DBWampApi()
        self.service._extract_namespace = mock.MagicMock(return_value='test.namespace')
        self.db = self.service._client.get_namespace('test.namespace')
        self.collection = 'coll'
        self.fake = Faker()
        self.fake.seed(4321)
        # self.service._client.get_namespace = mock.MagicMock(return_value=self.service._client._client['test.namespace'])

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

        wait_for_completion.wait_for_completion = True

    def tearDown(self):
        wait_for_completion.wait_for_completion = False

    def test_preInit(self):

        self.service.preInit()

        self.assertEqual(self.service.session_config_template, {})
        self.assertEqual(self.service.package_config_template, WampSchema('db', 'settings/settings'))
        self.assertEqual(self.service.session_config['loggernamespace'], 'db')

    def test_onInit(self):
        with mock.patch.dict('os.environ'):
            del os.environ['MD_MONGO_HOST']
            del os.environ['MD_MONGO_PORT']
            self.service.onInit()

            self.assertEqual(self.service._client._host, "localhost")
            self.assertEqual(self.service._client._port, 27017)
            self.assertEqual(self.service.autolog, False)
            self.assertEqual(self.service.autoschema, False)

    @mock.patch.dict(os.environ, {'MD_MONGO_HOST': 'localhost2'})
    def test_onInit_host(self):

        self.service.onInit()

        self.assertEqual(self.service._client._host, "localhost2")

    @mock.patch.dict(os.environ, {'MD_MONGO_PORT': '31312'})
    def test_onInit_port(self):

        self.service.onInit()

        self.assertEqual(self.service._client._port, 31312)

    @mock.patch.dict(os.environ, {'MD_MONGO_PORT': '31312'})
    def test_onRun(self):

        self.service.publish = mock.MagicMock()
        self.service.onRun(None)

        self.service.publish.assert_called_once_with(u'mdstudio.db.endpoint.events.online', True,
                                                     options=self.service.publish_options)

    @chainable
    def test_more(self):

        self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        cursor = yield self.db.find_many(self.collection, {})

        output = yield self.assertApi(self.service, 'more', {
            'cursorId': cursor['cursorId']
        })
        self.assertNotEqual(output['cursorId'], cursor['cursorId'])
        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': False,
            'results': [],
            'size': 0
        })

    @chainable
    def test_rewind(self):

        self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        cursor = yield self.db.find_many(self.collection, {})

        output = yield self.assertApi(self.service, 'rewind', {
            'cursorId': cursor['cursorId']
        })
        self.assertNotEqual(output['cursorId'], cursor['cursorId'])
        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': cursor['results'],
            'size': 2
        })

    @chainable
    def test_insert_one(self):

        for i in range(50):
            obj = self.fake.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            id = str(ObjectId())
            obj['_id'] = id
            output = yield self.assertApi(self.service, 'insert_one', {
                'collection': self.collection,
                'insert': obj,
            })
            self.assertEqual(output, {
                'id': id
            })
            found = yield self.db.find_one(self.collection, {'_id': id})
            self.assertEqual(obj, found['result'])

    @chainable
    def test_insert_one_fields_datetime(self):

        for i in range(50):
            obj = self.fake.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            id = str(ObjectId())
            date = self.fake.date_time().isoformat()
            obj['_id'] = id
            obj['datetimeField'] = date
            output = yield self.assertApi(self.service, 'insert_one', {
                'collection': self.collection,
                'insert': obj,
                'fields': {
                    'datetime': 'datetimeField'
                }
            })
            self.assertEqual(output, {
                'id': id
            })
            found = yield self.db.find_one(self.collection, {'_id': id})
            self.assertEqual(obj, found['result'])

    @chainable
    def test_insert_one_fields_datetime2(self):

        for i in range(50):
            obj = self.fake.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            id = str(ObjectId())
            date = self.fake.date_time()
            obj['_id'] = id
            obj['datetimeField'] = date
            output = yield self.assertApi(self.service, 'insert_one', {
                'collection': self.collection,
                'insert': obj,
                'fields': {
                    'datetime': 'datetimeField'
                }
            })
            self.assertEqual(output, {
                'id': id
            })
            obj['datetimeField'] = date.isoformat()
            found = yield self.db.find_one(self.collection, {'_id': id})
            self.assertEqual(obj, found['result'])

    @chainable
    def test_insert_many(self):

        for i in range(10):
            objs = []
            ids = []
            for j in range(self.fake.random_int(min=1, max=100)):
                obj = self.fake.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                id = str(ObjectId())
                obj['_id'] = id
                objs.append(obj)
                ids.append(id)
            output = yield self.assertApi(self.service, 'insert_many', {
                'collection': self.collection,
                'insert': objs
            })
            self.assertEqual(output, {
                'ids': ids
            })
            for j, fid in enumerate(ids):
                found = yield self.db.find_one(self.collection, {'_id': fid})
                self.assertEqual(objs[j], found['result'])

    @chainable
    def test_insert_many_fields_datetime(self):

        for i in range(10):
            objs = []
            ids = []
            for j in range(self.fake.random_int(min=1, max=100)):
                obj = self.fake.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                id = str(ObjectId())
                date = self.fake.date_time().isoformat()
                obj['_id'] = id
                obj['datetimeField'] = date
                objs.append(obj)
                ids.append(id)
            output = yield self.assertApi(self.service, 'insert_many', {
                'collection': self.collection,
                'insert': objs,
                'fields': {
                    'datetime': 'datetimeField'
                }
            })
            self.assertEqual(output, {
                'ids': ids
            })
            for j, fid in enumerate(ids):
                found = yield self.db.find_one(self.collection, {'_id': fid})
                self.assertEqual(objs[j], found['result'])

    @chainable
    def test_replace_one(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'replace_one', {
            'collection': self.collection,
            'filter': {'test': 2},
            'replacement': {
                'test2': 3
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @chainable
    def test_replace_one_upsert(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'replace_one', {
            'collection': self.collection,
            'filter': {'test': 2},
            'upsert': True,
            'replacement': {
                'test2': 3
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, {'test2': 3, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'matched': 0,
            'modified': 0,
            'upsertedId': cursor['results'][1]['_id']
        })

    @chainable
    def test_replace_one_fields_datetime(self):

        date3 = self.fake.date_time().isoformat()
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o3 = {'test2': 3, '_id': o2['_id'], 'date': date3}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'replace_one', {
            'collection': self.collection,
            'filter': {
                'test': 2
            },
            'replacement': {
                'test2': 3,
                'date': date3
            },
            'fields': {
                'datetime': ['date']
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @chainable
    def test_count_cursor_id(self):

        self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        cursor = yield self.db.find_many(self.collection, {})
        output = yield self.assertApi(self.service, 'count', {
            'collection': self.collection,
            'cursorId': cursor['cursorId'],
            'withLimitAndSkip': True
        })

        self.assertEqual(output, {'total': 2})

    @chainable
    def test_count_filter(self):

        self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        output = yield self.assertApi(self.service, 'count', {
            'collection': self.collection,
            'filter': {'test': {'$gt': 1}},
        })

        self.assertEqual(output, {'total': 1})

    @chainable
    def test_count_skip(self):

        self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        output = yield self.assertApi(self.service, 'count', {
            'collection': self.collection,
            'skip': 1
        })

        self.assertEqual(output, {'total': 1})

    @chainable
    def test_count_limit(self):

        self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        output = yield self.assertApi(self.service, 'count', {
            'collection': self.collection,
            'limit': 1
        })

        self.assertEqual(output, {'total': 1})

    @chainable
    def test_count_fields_datetime(self):

        self.db.insert_many(self.collection, [{'test': 1, 'date': self.fake.date_time().isoformat()},
                                              {'test': 2, 'date': self.fake.date_time().isoformat()}])
        output = yield self.assertApi(self.service, 'count', {
            'collection': self.collection,
            'limit': 1,
            'fields': {
                'datetime': ['date']
            }
        })

        self.assertEqual(output, {'total': 1})

    @chainable
    def test_update_one(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'update_one', {
            'collection': self.collection,
            'filter': {'test': 2},
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @chainable
    def test_update_one_upsert(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'update_one', {
            'collection': self.collection,
            'filter': {'test': 2},
            'upsert': True,
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, {'test2': 3, 'test': 2, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'matched': 0,
            'modified': 0,
            'upsertedId': cursor['results'][1]['_id']
        })

    @chainable
    def test_update_one_fields_datetime(self):

        date3 = self.fake.date_time().isoformat()
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id'], 'date': date3}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'update_one', {
            'collection': self.collection,
            'filter': {
                'test': 2
            },
            'update': {
                '$set': {
                    'test2': 3,
                    'date': date3
                }
            },
            'fields': {
                'datetime': ['date']
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @chainable
    def test_update_many(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'update_many', {
            'collection': self.collection,
            'filter': {'test': 2},
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @chainable
    def test_update_many_upsert(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'update_many', {
            'collection': self.collection,
            'filter': {'test': 2},
            'upsert': True,
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, {'test2': 3, 'test': 2, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'matched': 0,
            'modified': 0,
            'upsertedId': cursor['results'][1]['_id']
        })

    @chainable
    def test_update_many_fields_datetime(self):

        date3 = self.fake.date_time().isoformat()
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id'], 'date': date3}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'update_many', {
            'collection': self.collection,
            'filter': {
                'test': 2
            },
            'update': {
                '$set': {
                    'test2': 3,
                    'date': date3
                }
            },
            'fields': {
                'datetime': ['date']
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @chainable
    def test_find_one(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'filter': {'test': 1}
        })

        self.assertEqual(output, {
            'result': objs[1]
        })

    @chainable
    def test_find_one_projection(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'filter': {'test': 1},
            'projection': {'_id': 0}
        })

        self.assertEqual(output, {
            'result': {'test': 1}
        })

    @chainable
    def test_find_one_skip(self):

        objs = [{
            'test': 1,
            '_id': str(ObjectId())
        }]
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'filter': {'test': 1},
            'skip': 1
        })

        self.assertEqual(output, {
            'result': objs[2]
        })

    @chainable
    def test_find_one_sort(self):

        objs = [{
            'test': 1,
            '_id': str(ObjectId())
        }]
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'filter': {'test': 1},
            'sort': [
                ['_id', 'desc']
            ]
        })

        self.assertEqual(output, {
            'result': objs[2]
        })

    @chainable
    def test_find_one_fields_datetime(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId()),
                'date': self.fake.date_time().isoformat()
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'filter': {'test': 1},
            'fields': {
                'datetime': ['date']
            }
        })

        self.assertEqual(output, {
            'result': objs[1]
        })

    @chainable
    def test_find_many(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'filter': {'test': 1}
        })

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[1]],
            'size': 1
        })

    @chainable
    def test_find_many_projection(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'filter': {'test': 1},
            'projection': {'_id': 0}
        })

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [{'test': 1}],
            'size': 1
        })

    @chainable
    def test_find_many_skip(self):

        objs = [{
            'test': 1,
            '_id': str(ObjectId())
        }]
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'filter': {'test': 1},
            'skip': 1
        })

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[2]],
            'size': 1
        })

    @chainable
    def test_find_many_limit(self):

        objs = [{
            'test': 1,
            '_id': str(ObjectId())
        }]
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'filter': {'test': 1},
            'limit': 1
        })

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[0]],
            'size': 1
        })

    @chainable
    def test_find_many_sort(self):

        objs = [{
            'test': 1,
            '_id': str(ObjectId())
        }]
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'filter': {'test': 1},
            'sort': [
                ['_id', 'desc']
            ]
        })

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[2], objs[0]],
            'size': 2
        })

    @chainable
    def test_find_many_fields_datetime(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId()),
                'date': self.fake.date_time().isoformat()
            })
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'filter': {'test': 1},
            'fields': {
                'datetime': ['date']
            }
        })

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[1]],
            'size': 1
        })

    @chainable
    def test_find_one_and_update(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'filter': {'test': 2},
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o2
        })

    @chainable
    def test_find_one_and_update_projection(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'filter': {'test': 2},
            'projection': {
                '_id': 0
            },
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': {'test': 2}
        })

    @chainable
    def test_find_one_and_update_sort(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1, o2, o3])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'filter': {'test': 2},
            'sort': [
                ['_id', "desc"]
            ],
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        })
        self.assertEqual(output, {
            'result': o3
        })
        cursor = yield self.db.find_many(self.collection, {})
        o3['test2'] = 3
        self.assertSequenceEqual(cursor['results'], [o1, o2, o3])

    @chainable
    def test_find_one_and_update_return_updated(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'filter': {'test': 2},
            'returnUpdated': True,
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o3
        })

    @chainable
    def test_find_one_and_update_upsert(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'filter': {'test': 2},
            'upsert': True,
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'],
                                 [o1, {'test2': 3, 'test': 2, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'result': None
        })

    @chainable
    def test_find_one_and_update_fields_datetime(self):
        date3 = self.fake.date_time().isoformat()
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id'], 'date': date3}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'filter': {
                'test': 2
            },
            'update': {
                '$set': {
                    'test2': 3,
                    'date': date3
                }
            },
            'fields': {
                'datetime': ['date']
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o2
        })

    @chainable
    def test_find_one_and_replace(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'filter': {'test': 2},
            'replacement': {
                'test2': 3
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o2
        })

    @chainable
    def test_find_one_and_replace_projection(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'filter': {'test': 2},
            'projection': {
                '_id': 0
            },
            'replacement': {
                'test2': 3
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': {'test': 2}
        })

    @chainable
    def test_find_one_and_replace_sort(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1, o2, o3])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'filter': {'test': 2},
            'sort': [
                ['_id', "desc"]
            ],
            'replacement': {
                'test2': 3
            }
        })
        self.assertEqual(output, {
            'result': o3
        })
        cursor = yield self.db.find_many(self.collection, {})
        o3['test2'] = 3
        self.assertSequenceEqual(cursor['results'], [o1, o2, {'test2': 3, '_id': o3['_id']}])

    @chainable
    def test_find_one_and_replace_return_updated(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'filter': {'test': 2},
            'returnUpdated': True,
            'replacement': {
                'test2': 3
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o3
        })

    @chainable
    def test_find_one_and_replace_upsert(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'filter': {'test': 2},
            'upsert': True,
            'replacement': {
                'test2': 3
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'],
                                 [o1, {'test2': 3, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'result': None
        })

    @chainable
    def test_find_one_and_replace_fields_datetime(self):
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o3 = {'test2': 3, '_id': o2['_id']}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'filter': {
                'test': 2
            },
            'replacement': {
                'test2': 3
            },
            'fields': {
                'datetime': ['date']
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o2
        })

    @chainable
    def test_find_one_and_delete(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_delete', {
            'collection': self.collection,
            'filter': {'test': 2}
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1])
        self.assertEqual(output, {
            'result': o2
        })

    @chainable
    def test_find_one_and_delete_projection(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_delete', {
            'collection': self.collection,
            'filter': {'test': 2},
            'projection': {
                '_id': 0
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1])
        self.assertEqual(output, {
            'result': {'test': 2}
        })

    @chainable
    def test_find_one_and_delete_sort(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, '_id': str(ObjectId())}
        self.db.insert_many(self.collection, [o1, o2, o3])
        output = yield self.assertApi(self.service, 'find_one_and_delete', {
            'collection': self.collection,
            'filter': {'test': 2},
            'sort': [
                ['_id', "desc"]
            ]
        })
        self.assertEqual(output, {
            'result': o3
        })
        cursor = yield self.db.find_many(self.collection, {})
        o3['test2'] = 3
        self.assertSequenceEqual(cursor['results'], [o1, o2])

    @chainable
    def test_find_one_and_delete_fields_datetime(self):
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_delete', {
            'collection': self.collection,
            'filter': {
                'test': 2
            },
            'fields': {
                'datetime': ['date']
            }
        })
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1])
        self.assertEqual(output, {
            'result': o2
        })

    @chainable
    def test_distinct(self):

        self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}, {'test': 3}, {'test': 2}])
        output = yield self.assertApi(self.service, 'distinct', {
            'collection': self.collection,
            'field': 'test'
        })
        self.assertEqual(output, {
            'results': [1, 2, 3],
            'total': 3
        })

    @chainable
    def test_distinct_filter(self):

        self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}, {'test': 3}, {'test': 2}])
        output = yield self.assertApi(self.service, 'distinct', {
            'collection': self.collection,
            'field': 'test',
            'filter': {
                'test': {
                    '$gt': 1
                }
            }
        })
        self.assertEqual(output, {
            'results': [2, 3],
            'total': 2
        })

    @chainable
    def test_distinct_field_datetime(self):

        self.db.insert_many(self.collection, [
            {'test': 1, 'date': self.fake.date_time().isoformat()},
            {'test': 2, 'date': self.fake.date_time().isoformat()},
            {'test': 3, 'date': self.fake.date_time().isoformat()},
            {'test': 2, 'date': self.fake.date_time().isoformat()}])
        output = yield self.assertApi(self.service, 'distinct', {
            'collection': self.collection,
            'field': 'test',
            'fields': {
                'datetime': ['date']
            }
        })
        self.assertEqual(output, {
            'results': [1, 2, 3],
            'total': 3
        })

    @chainable
    def test_aggregate(self):
        objs = [
            {'test': 1, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())},
            {'test': 3, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())}
        ]
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'aggregate', {
            'collection': self.collection,
            'pipeline': [
                {
                    '$match': {'test': {'$gt': 1}}
                }
            ]
        })
        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': objs[1:],
            'size': 3
        })

    @chainable
    def test_delete_one(self):
        objs = [
            {'test': 1, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())},
            {'test': 3, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())}
        ]
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'delete_one', {
            'collection': self.collection,
            'filter': {
                'test': 2
            }
        })

        self.assertEqual(output, {
            'count': 1
        })

        cursor = yield self.db.find_many(self.collection, {})
        self.assertIsInstance(cursor['cursorId'], str)
        del cursor['cursorId']
        self.assertEqual(cursor, {
            'alive': True,
            'results': [objs[0], objs[2], objs[3]],
            'size': 3
        })

    @chainable
    def test_delete_one_date_fields(self):
        objs = [
            {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()},
            {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()},
            {'test': 3, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()},
            {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        ]
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'delete_one', {
            'collection': self.collection,
            'filter': {
                'test': 2
            },
            'fields': {
                'datetime': ['date']
            }
        })

        self.assertEqual(output, {
            'count': 1
        })

        cursor = yield self.db.find_many(self.collection, {})
        self.assertIsInstance(cursor['cursorId'], str)
        del cursor['cursorId']
        self.assertEqual(cursor, {
            'alive': True,
            'results': [objs[0], objs[2], objs[3]],
            'size': 3
        })

    @chainable
    def test_delete_many(self):
        objs = [
            {'test': 1, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())},
            {'test': 3, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())}
        ]
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'delete_many', {
            'collection': self.collection,
            'filter': {
                'test': 2
            }
        })

        self.assertEqual(output, {
            'count': 2
        })

        cursor = yield self.db.find_many(self.collection, {})
        self.assertIsInstance(cursor['cursorId'], str)
        del cursor['cursorId']
        self.assertEqual(cursor, {
            'alive': True,
            'results': [objs[0], objs[2]],
            'size': 2
        })

    @chainable
    def test_delete_many_date_fields(self):
        objs = [
            {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()},
            {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()},
            {'test': 3, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()},
            {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time().isoformat()}
        ]
        self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'delete_many', {
            'collection': self.collection,
            'filter': {
                'test': 2
            },
            'fields': {
                'datetime': ['date']
            }
        })

        self.assertEqual(output, {
            'count': 2
        })

        cursor = yield self.db.find_many(self.collection, {})
        self.assertIsInstance(cursor['cursorId'], str)
        del cursor['cursorId']
        self.assertEqual(cursor, {
            'alive': True,
            'results': [objs[0], objs[2]],
            'size': 2
        })

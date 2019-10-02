import os
import pytz
from faker import Faker
from mock import mock, call
from mongomock import ObjectId
from twisted.internet import reactor

from db.application import DBComponent
from db.key_repository import KeyRepository
from mdstudio.db.fields import Fields
from mdstudio.deferred.chainable import test_chainable
from mdstudio.deferred.lock import Lock
from mdstudio.unittest.api import APITestCase
from mdstudio.unittest.db import DBTestCase
from mdstudio.unittest.settings import load_settings


class TestDBComponent(DBTestCase, APITestCase):
    fake = Faker()

    def setUp(self):
        with load_settings(DBComponent, {
                'settings': {
                    'port': 27017,
                    'host': 'localhost',
                    'secret': self.fake.pystr(20)
                }
            }):
            self.service = DBComponent()

        self.db = self.service._client.get_database('users~userNameDatabase')
        self.claims = {
            'connectionType': 'user',
            'username': 'userNameDatabase'
        }
        self.collection = 'coll'

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

    @mock.patch.dict(os.environ, {'MD_MONGO_HOST': 'localhost2', 'MD_MONGO_PORT': '31312'})
    @mock.patch("mdstudio.component.impl.core.CoreComponentSession.pre_init")
    def test_pre_init_host(self, m):
        self.service.component_config = self.service.Config()

        self.service.pre_init()

        self.assertEqual(self.service._client._host, "localhost2")
        self.assertEqual(self.service._client._port, 31312)
        m.assert_called_once()


    def test_on_init(self):

        self.service.component_config.settings['secret'] = 'test secret test secrets test'
        self.service.on_init()
        self.assertIsInstance(self.service._secret, bytes)
        self.assertEqual(self.service._secret, b'pJIM5xrgbis_h9HBqfexTSf7MON0uedITnyPdI67ngY=')
        self.assertIsInstance(self.service.database_lock, Lock)

    @mock.patch("mdstudio.component.impl.core.CoreComponentSession._on_join")
    @test_chainable
    def test_on_join(self, m):

        self.service.call = mock.MagicMock()
        yield self.service._on_join()
        self.service.call.assert_has_calls([
            call('mdstudio.auth.endpoint.ring0.set-status', {'status': True})
        ])
        m.assert_called_once()

    @test_chainable
    def test_more(self):

        yield self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        cursor = yield self.db.find_many(self.collection, {})

        output = yield self.assertApi(self.service, 'more', {
            'cursorId': cursor['cursorId']
        }, self.claims)
        self.assertNotEqual(output['cursorId'], cursor['cursorId'])
        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': False,
            'results': [],
            'size': 0
        })

    @test_chainable
    def test_rewind(self):

        yield self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        cursor = yield self.db.find_many(self.collection, {})

        output = yield self.assertApi(self.service, 'rewind', {
            'cursorId': cursor['cursorId']
        }, self.claims)
        self.assertNotEqual(output['cursorId'], cursor['cursorId'])
        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': cursor['results'],
            'size': 2
        })

    @test_chainable
    def test_insert_one(self):

        for i in range(50):
            obj = self.fake.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            id = str(ObjectId())
            obj['_id'] = id
            output = yield self.assertApi(self.service, 'insert_one', {
                'collection': self.collection,
                'insert': obj,
            }, self.claims)
            self.assertEqual(output, {
                'id': id
            })
            found = yield self.db.find_one(self.collection, {'_id': id})
            self.assertEqual(obj, found['result'])

    @test_chainable
    def test_insert_one_fields_datetime(self):

        for i in range(50):
            obj = self.fake.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            id = str(ObjectId())
            date = self.fake.date_time(tzinfo=pytz.utc).isoformat()
            obj['_id'] = id
            obj['datetimeField'] = date
            output = yield self.assertApi(self.service, 'insert_one', {
                'collection': self.collection,
                'insert': obj,
                'fields': {
                    'datetime': 'datetimeField'
                }
            }, self.claims)
            self.assertEqual(output, {
                'id': id
            })
            found = yield self.db.find_one(self.collection, {'_id': id}, fields=Fields(date_times=['datetimeField']))
            self.assertEqual(obj, found['result'])

    @test_chainable
    def test_insert_one_fields_datetime2(self):

        for i in range(50):
            obj = self.fake.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            id = str(ObjectId())
            date = self.fake.date_time(tzinfo=pytz.utc).isoformat()
            obj['_id'] = id
            obj['datetimeField'] = date
            output = yield self.assertApi(self.service, 'insert_one', {
                'collection': self.collection,
                'insert': obj,
                'fields': {
                    'datetime': 'datetimeField'
                }
            }, self.claims)
            self.assertEqual(output, {
                'id': id
            })
            found = yield self.db.find_one(self.collection, {'_id': id}, fields=Fields(date_times=['datetimeField']))
            self.assertEqual(obj, found['result'])

    @test_chainable
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
            }, self.claims)
            self.assertEqual(output, {
                'ids': ids
            })
            for j, fid in enumerate(ids):
                found = yield self.db.find_one(self.collection, {'_id': fid})
                self.assertEqual(objs[j], found['result'])

    @test_chainable
    def test_insert_many_fields_datetime(self):

        for i in range(10):
            objs = []
            ids = []
            for j in range(self.fake.random_int(min=1, max=100)):
                obj = self.fake.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                id = str(ObjectId())
                date = self.fake.date_time(tzinfo=pytz.utc).isoformat()
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
            }, self.claims)
            self.assertEqual(output, {
                'ids': ids
            })
            for j, fid in enumerate(ids):
                found = yield self.db.find_one(self.collection, {'_id': fid}, fields=Fields(date_times=['datetimeField']))
                self.assertEqual(objs[j], found['result'])

    @test_chainable
    def test_replace_one(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'replace_one', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'replacement': {
                'test2': 3
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @test_chainable
    def test_replace_one_upsert(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'replace_one', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'upsert': True,
            'replacement': {
                'test2': 3
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, {'test2': 3, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'matched': 0,
            'modified': 0,
            'upsertedId': cursor['results'][1]['_id']
        })

    @test_chainable
    def test_replace_one_fields_datetime(self):

        date3 = self.fake.date_time(tzinfo=pytz.utc)
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc)}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc)}
        o3 = {'test2': 3, '_id': o2['_id'], 'date': date3}
        yield self.db.insert_many(self.collection, [o1, o2], fields=Fields(date_times=['date']))
        output = yield self.assertApi(self.service, 'replace_one', {
            'collection': self.collection,
            'dbfilter': {
                'test': 2
            },
            'replacement': {
                'test2': 3,
                'date': date3
            },
            'fields': {
                'datetime': ['date']
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {}, fields=Fields(date_times=['date']))
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @test_chainable
    def test_count_filter(self):

        yield self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        output = yield self.assertApi(self.service, 'count', {
            'collection': self.collection,
            'dbfilter': {'test': {'$gt': 1}},
        }, self.claims)

        self.assertEqual(output, {'total': 1})

    @test_chainable
    def test_count_skip(self):

        yield self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        output = yield self.assertApi(self.service, 'count', {
            'collection': self.collection,
            'skip': 1
        }, self.claims)

        self.assertEqual(output, {'total': 1})

    @test_chainable
    def test_count_limit(self):

        yield self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        output = yield self.assertApi(self.service, 'count', {
            'collection': self.collection,
            'limit': 1
        }, self.claims)

        self.assertEqual(output, {'total': 1})

    @test_chainable
    def test_count_fields_datetime(self):

        yield self.db.insert_many(self.collection, [{'test': 1, 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
                                                    {'test': 2, 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}])
        output = yield self.assertApi(self.service, 'count', {
            'collection': self.collection,
            'limit': 1,
            'fields': {
                'datetime': ['date']
            }
        }, self.claims)

        self.assertEqual(output, {'total': 1})

    @test_chainable
    def test_count_cursor_id(self):
        yield self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}])
        cursor = yield self.db.find_many(self.collection, {})

        output = yield self.assertApi(self.service, 'count', {
            'cursorId': cursor['cursorId'],
            'withLimitAndSkip': True
        }, self.claims)
        self.assertEqual(output, {
            'total': 2
        })

    @test_chainable
    def test_update_one(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'update_one', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @test_chainable
    def test_update_one_upsert(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'update_one', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'upsert': True,
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, {'test2': 3, 'test': 2, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'matched': 0,
            'modified': 0,
            'upsertedId': cursor['results'][1]['_id']
        })

    @test_chainable
    def test_update_one_fields_datetime(self):

        date3 = self.fake.date_time(tzinfo=pytz.utc)
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id'], 'date': date3}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'update_one', {
            'collection': self.collection,
            'dbfilter': {
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
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @test_chainable
    def test_update_many(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'update_many', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @test_chainable
    def test_update_many_upsert(self):

        o1 = {'test': 1, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'update_many', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'upsert': True,
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, {'test2': 3, 'test': 2, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'matched': 0,
            'modified': 0,
            'upsertedId': cursor['results'][1]['_id']
        })

    @test_chainable
    def test_update_many_fields_datetime(self):

        date3 = self.fake.date_time(tzinfo=pytz.utc)
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id'], 'date': date3}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'update_many', {
            'collection': self.collection,
            'dbfilter': {
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
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'matched': 1,
            'modified': 1
        })

    @test_chainable
    def test_find_one(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'dbfilter': {'test': 1}
        }, self.claims)

        self.assertEqual(output, {
            'result': objs[1]
        })

    @test_chainable
    def test_find_one_projection(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'dbfilter': {'test': 1},
            'projection': {'_id': 0}
        }, self.claims)

        self.assertEqual(output, {
            'result': {'test': 1}
        })

    @test_chainable
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
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'dbfilter': {'test': 1},
            'skip': 1
        }, self.claims)

        self.assertEqual(output, {
            'result': objs[2]
        })

    @test_chainable
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
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'dbfilter': {'test': 1},
            'sort': [
                ['_id', 'desc']
            ]
        }, self.claims)

        self.assertEqual(output, {
            'result': objs[2]
        })

    @test_chainable
    def test_find_one_fields_datetime(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId()),
                'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()
            })
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_one', {
            'collection': self.collection,
            'dbfilter': {'test': 1},
            'fields': {
                'datetime': ['date']
            }
        }, self.claims)

        self.assertEqual(output, {
            'result': objs[1]
        })

    @test_chainable
    def test_find_many(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'dbfilter': {'test': 1}
        }, self.claims)

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[1]],
            'size': 1
        })

    @test_chainable
    def test_find_many_projection(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId())
            })
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'dbfilter': {'test': 1},
            'projection': {'_id': 0}
        }, self.claims)

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [{'test': 1}],
            'size': 1
        })

    @test_chainable
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
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'dbfilter': {'test': 1},
            'skip': 1
        }, self.claims)

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[2]],
            'size': 1
        })

    @test_chainable
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
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'dbfilter': {'test': 1},
            'limit': 1
        }, self.claims)

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[0]],
            'size': 1
        })

    @test_chainable
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
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'dbfilter': {'test': 1},
            'sort': [
                ['_id', 'desc']
            ]
        }, self.claims)

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[2], objs[0]],
            'size': 2
        })

    @test_chainable
    def test_find_many_fields_datetime(self):

        objs = []
        for i in range(20):
            objs.append({
                'test': i,
                '_id': str(ObjectId()),
                'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()
            })
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'find_many', {
            'collection': self.collection,
            'dbfilter': {'test': 1},
            'fields': {
                'datetime': ['date']
            }
        }, self.claims)

        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': [objs[1]],
            'size': 1
        })

    @test_chainable
    def test_find_one_and_update(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o2
        })

    @test_chainable
    def test_find_one_and_update_projection(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'projection': {
                '_id': 0
            },
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': {'test': 2}
        })

    @test_chainable
    def test_find_one_and_update_sort(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1, o2, o3])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'sort': [
                ['_id', "desc"]
            ],
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        }, self.claims)
        self.assertEqual(output, {
            'result': o3
        })
        cursor = yield self.db.find_many(self.collection, {})
        o3['test2'] = 3
        self.assertSequenceEqual(cursor['results'], [o1, o2, o3])

    @test_chainable
    def test_find_one_and_update_return_updated(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'returnUpdated': True,
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o3
        })

    @test_chainable
    def test_find_one_and_update_upsert(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'upsert': True,
            'update': {
                '$set': {
                    'test2': 3
                }
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'],
                                 [o1, {'test2': 3, 'test': 2, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'result': None
        })

    @test_chainable
    def test_find_one_and_update_fields_datetime(self):
        date3 = self.fake.date_time(tzinfo=pytz.utc)
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        o3 = {'test': 2, 'test2': 3, '_id': o2['_id'], 'date': date3}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_update', {
            'collection': self.collection,
            'dbfilter': {
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
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o2
        })

    @test_chainable
    def test_find_one_and_replace(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'replacement': {
                'test2': 3
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o2
        })

    @test_chainable
    def test_find_one_and_replace_projection(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'projection': {
                '_id': 0
            },
            'replacement': {
                'test2': 3
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': {'test': 2}
        })

    @test_chainable
    def test_find_one_and_replace_sort(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1, o2, o3])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'sort': [
                ['_id', "desc"]
            ],
            'replacement': {
                'test2': 3
            }
        }, self.claims)
        self.assertEqual(output, {
            'result': o3
        })
        cursor = yield self.db.find_many(self.collection, {})
        o3['test2'] = 3
        self.assertSequenceEqual(cursor['results'], [o1, o2, {'test2': 3, '_id': o3['_id']}])

    @test_chainable
    def test_find_one_and_replace_return_updated(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'returnUpdated': True,
            'replacement': {
                'test2': 3
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o3
        })

    @test_chainable
    def test_find_one_and_replace_upsert(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'upsert': True,
            'replacement': {
                'test2': 3
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'],
                                 [o1, {'test2': 3, '_id': cursor['results'][1]['_id']}])
        self.assertEqual(output, {
            'result': None
        })

    @test_chainable
    def test_find_one_and_replace_fields_datetime(self):
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        o3 = {'test2': 3, '_id': o2['_id']}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_replace', {
            'collection': self.collection,
            'dbfilter': {
                'test': 2
            },
            'replacement': {
                'test2': 3
            },
            'fields': {
                'datetime': ['date']
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1, o3])
        self.assertEqual(output, {
            'result': o2
        })

    @test_chainable
    def test_find_one_and_delete(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_delete', {
            'collection': self.collection,
            'dbfilter': {'test': 2}
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1])
        self.assertEqual(output, {
            'result': o2
        })

    @test_chainable
    def test_find_one_and_delete_projection(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_delete', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'projection': {
                '_id': 0
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1])
        self.assertEqual(output, {
            'result': {'test': 2}
        })

    @test_chainable
    def test_find_one_and_delete_sort(self):
        o1 = {'test': 1, '_id': str(ObjectId())}
        o2 = {'test': 2, '_id': str(ObjectId())}
        o3 = {'test': 2, '_id': str(ObjectId())}
        yield self.db.insert_many(self.collection, [o1, o2, o3])
        output = yield self.assertApi(self.service, 'find_one_and_delete', {
            'collection': self.collection,
            'dbfilter': {'test': 2},
            'sort': [
                ['_id', "desc"]
            ]
        }, self.claims)
        self.assertEqual(output, {
            'result': o3
        })
        cursor = yield self.db.find_many(self.collection, {})
        o3['test2'] = 3
        self.assertSequenceEqual(cursor['results'], [o1, o2])

    @test_chainable
    def test_find_one_and_delete_fields_datetime(self):
        o1 = {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        o2 = {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        yield self.db.insert_many(self.collection, [o1, o2])
        output = yield self.assertApi(self.service, 'find_one_and_delete', {
            'collection': self.collection,
            'dbfilter': {
                'test': 2
            },
            'fields': {
                'datetime': ['date']
            }
        }, self.claims)
        cursor = yield self.db.find_many(self.collection, {})
        self.assertSequenceEqual(cursor['results'], [o1])
        self.assertEqual(output, {
            'result': o2
        })

    @test_chainable
    def test_distinct_filter(self):

        yield self.db.insert_many(self.collection, [{'test': 1}, {'test': 2}, {'test': 3}, {'test': 2}])
        output = yield self.assertApi(self.service, 'distinct', {
            'collection': self.collection,
            'field': 'test',
            'dbfilter': {
                'test': {
                    '$gt': 1
                }
            }
        }, self.claims)
        self.assertEqual(output, {
            'results': [2, 3],
            'total': 2
        })

    @test_chainable
    def test_distinct_field_datetime(self):

        yield self.db.insert_many(self.collection, [
            {'test': 1, 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
            {'test': 2, 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
            {'test': 3, 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
            {'test': 2, 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}])
        output = yield self.assertApi(self.service, 'distinct', {
            'collection': self.collection,
            'field': 'test',
            'fields': {
                'datetime': ['date']
            }
        }, self.claims)
        self.assertEqual(output, {
            'results': [1, 2, 3],
            'total': 3
        })

    @test_chainable
    def test_aggregate(self):
        objs = [
            {'test': 1, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())},
            {'test': 3, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())}
        ]
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'aggregate', {
            'collection': self.collection,
            'pipeline': [
                {
                    '$match': {'test': {'$gt': 1}}
                }
            ]
        }, self.claims)
        self.assertIsInstance(output['cursorId'], str)
        del output['cursorId']
        self.assertEqual(output, {
            'alive': True,
            'results': objs[1:],
            'size': 3
        })

    @test_chainable
    def test_delete_one(self):
        objs = [
            {'test': 1, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())},
            {'test': 3, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())}
        ]
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'delete_one', {
            'collection': self.collection,
            'dbfilter': {
                'test': 2
            }
        }, self.claims)

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

    @test_chainable
    def test_delete_one_date_fields(self):
        objs = [
            {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
            {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
            {'test': 3, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
            {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        ]
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'delete_one', {
            'collection': self.collection,
            'dbfilter': {
                'test': 2
            },
            'fields': {
                'datetime': ['date']
            }
        }, self.claims)

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

    @test_chainable
    def test_delete_many(self):
        objs = [
            {'test': 1, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())},
            {'test': 3, '_id': str(ObjectId())},
            {'test': 2, '_id': str(ObjectId())}
        ]
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'delete_many', {
            'collection': self.collection,
            'dbfilter': {
                'test': 2
            }
        }, self.claims)

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

    @test_chainable
    def test_delete_many_date_fields(self):
        objs = [
            {'test': 1, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
            {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
            {'test': 3, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()},
            {'test': 2, '_id': str(ObjectId()), 'date': self.fake.date_time(tzinfo=pytz.utc).isoformat()}
        ]
        yield self.db.insert_many(self.collection, objs)
        output = yield self.assertApi(self.service, 'delete_many', {
            'collection': self.collection,
            'dbfilter': {
                'test': 2
            },
            'fields': {
                'datetime': ['date']
            }
        }, self.claims)

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

    @test_chainable
    def test_get_database(self):
        self.assertEqual((yield self.service.get_database({
            'connectionType': 'user',
            'username': 'test-user'
        }))._database_name, 'users~test-user')

    @test_chainable
    def test_get_database2(self):
        for i in range(50):
            word = self.fake.word()
            self.assertEqual((yield self.service.get_database({
                'connectionType': 'user',
                'username': word
            }))._database_name, 'users~{}'.format(word))

    @test_chainable
    def test_get_database3(self):
        self.assertEqual((yield self.service.get_database({
            'connectionType': 'group',
            'group': 'test-group'
        }))._database_name, 'groups~test-group')

    @test_chainable
    def test_get_database4(self):
        for i in range(50):
            word = self.fake.word()
            self.assertEqual((yield self.service.get_database({
                'connectionType': 'group',
                'group': word
            }))._database_name, 'groups~{}'.format(word))

    @test_chainable
    def test_get_database5(self):
        self.assertEqual((yield self.service.get_database({
            'connectionType': 'groupRole',
            'group': 'test-group',
            'role': 'test-group-role'
        }))._database_name, 'grouproles~test-group~test-group-role')

    @test_chainable
    def test_get_database6(self):
        for i in range(50):
            word = self.fake.word()
            role = self.fake.word()
            self.assertEqual((yield self.service.get_database({
                'connectionType': 'groupRole',
                'group': word,
                'role': role
            }))._database_name, 'grouproles~{}~{}'.format(word, role))

    @test_chainable
    def test_get_database_non_existing(self):
        yield self.assertFailure(self.service.get_database({
            'connectionType': 'groupRoles',
            'group': 'test-group',
            'role': 'test-group-role'
        }), ValueError)

    def test_set_fields(self):
        claims = {'test': 'hello worlds'}
        kwargs = {}
        self.service.set_fields(claims, kwargs, {
            'fields': {
                'encrypted': ['test']
            }
        })
        self.assertEqual(kwargs['fields'], Fields(encrypted=['test']))
        self.assertIsInstance(kwargs['fields']._key_repository, KeyRepository)
        self.assertEqual(kwargs['claims'], claims)

from datetime import datetime, timedelta

from faker import Faker
from twisted.internet import reactor

from schema.application import SchemaComponent
from schema.exception import SchemaException
from schema.schema_repository import SchemaRepository
from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from mdstudio.deferred.chainable import test_chainable
from mdstudio.unittest.db import DBTestCase
from mdstudio.utc import now


class TestSchemaRepository(DBTestCase):
    fake = Faker()

    def setUp(self):

        self.service = SchemaComponent()
        self.type = self.fake.word()
        self.db = MongoClientWrapper("localhost", 27127).get_database('users~schemaTest')
        self.rep = SchemaRepository(self.db, self.type)
        self.claims = {
            'username': self.fake.user_name(),
            'group': self.fake.user_name()
        }

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

    def test_construction(self):
        self.assertEqual(self.db, self.rep.wrapper)
        self.assertEqual(self.type, self.rep.type)

    @test_chainable
    def test_upsert(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
            }
        }, self.claims)

        uploaded = yield self.rep.find_latest(vendor, component, name, version)
        self.assertIsInstance(uploaded['updatedAt'], datetime)
        self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
        expected = {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'updatedAt': uploaded['updatedAt'],
            'build': 1,
            'schema': '{}',
            'hash': self.rep.hash_schema('{}')
        }
        self.assertEqual(uploaded, expected)

        found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
        self.assertEqual(found, expected)

        found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})['result']
        self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
        del found_history['builds'][0]['createdAt']
        self.assertEqual(found_history, {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'builds': [
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'c89a148be40e6752261e3038609a4b68de22fa3bfdaf32f884edffb8480b9bbe',
                    'schema': '{}'
                }
            ]
        })

    @test_chainable
    def test_upsert_same_twice(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
            }
        }, self.claims)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
            }
        }, self.claims)

        uploaded = yield self.rep.find_latest(vendor, component, name, version)
        self.assertIsInstance(uploaded['updatedAt'], datetime)
        self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
        expected = {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'updatedAt': uploaded['updatedAt'],
            'build': 1,
            'schema': '{}',
            'hash': self.rep.hash_schema('{}')
        }
        self.assertEqual(uploaded, expected)

        found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
        self.assertEqual(found, expected)

        found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})['result']
        self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
        del found_history['builds'][0]['createdAt']
        self.assertEqual(found_history, {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'builds': [
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'c89a148be40e6752261e3038609a4b68de22fa3bfdaf32f884edffb8480b9bbe',
                    'schema': '{}'
                }
            ]
        })

    @test_chainable
    def test_upsert_same_trice(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
            }
        }, self.claims)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
            }
        }, self.claims)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
            }
        }, self.claims)

        uploaded = yield self.rep.find_latest(vendor, component, name, version)
        self.assertIsInstance(uploaded['updatedAt'], datetime)
        self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
        expected = {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'updatedAt': uploaded['updatedAt'],
            'build': 1,
            'schema': '{}',
            'hash': self.rep.hash_schema('{}')
        }
        self.assertEqual(uploaded, expected)

        found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
        self.assertEqual(found, expected)

        found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})['result']
        self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
        del found_history['builds'][0]['createdAt']
        self.assertEqual(found_history, {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'builds': [
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'c89a148be40e6752261e3038609a4b68de22fa3bfdaf32f884edffb8480b9bbe',
                    'schema': '{}'
                }
            ]
        })

    @test_chainable
    def test_upsert_invalid(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)

        completed = False
        try:
            yield self.rep.upsert(vendor, component, {
                'name': name,
                'version': version,
                'schema': {
                    'type': 'any'
                }
            }, self.claims)
            completed = True
        except SchemaException as e:
            found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
            self.assertEqual(found, None)

            found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})['result']
            self.assertEqual(found_history, None)

            self.assertRegex(str(e), "Schema does not conform to jsonschema draft 4")
        self.assertFalse(completed)

    @test_chainable
    def test_upsert_new_incompatible(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
            }
        }, self.claims)

        completed = False
        try:
            yield self.rep.upsert(vendor, component, {
                'name': name,
                'version': version,
                'schema': {
                    '$schema': 'http://json-schema.org/schema#'
                }
            }, self.claims)
        except SchemaException as e:
            uploaded = yield self.rep.find_latest(vendor, component, name, version)
            self.assertIsInstance(uploaded['updatedAt'], datetime)
            self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
            expected = {
                'name': name,
                'version': version,
                'vendor': vendor,
                'component': component,
                'updatedAt': uploaded['updatedAt'],
                'build': 1,
                'schema': '{}',
                'hash': self.rep.hash_schema('{}')
            }
            self.assertEqual(uploaded, expected)

            found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
            self.assertEqual(found, expected)

            found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})[
                'result']
            self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
            self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
            del found_history['builds'][0]['createdAt']
            self.assertEqual(found_history, {
                'name': name,
                'version': version,
                'vendor': vendor,
                'component': component,
                'builds': [
                    {
                        'createdBy': {
                            'group': self.claims['group'],
                            'username': self.claims['username']
                        },
                        'hash': 'c89a148be40e6752261e3038609a4b68de22fa3bfdaf32f884edffb8480b9bbe',
                        'schema': '{}'
                    }
                ]
            })

            self.assertRegex(str(e), "The new schema is not compatible with the old version that was "
                                     "already registered. Incompatible changes were")
        self.assertFalse(completed)

    @test_chainable
    def test_upsert_new_incompatible2(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
                '$schema': 'http://json-schema.org/schema#'
            }
        }, self.claims)

        completed = False
        try:
            yield self.rep.upsert(vendor, component, {
                'name': name,
                'version': version,
                'schema': {
                }
            }, self.claims)
        except SchemaException as e:
            uploaded = yield self.rep.find_latest(vendor, component, name, version)
            self.assertIsInstance(uploaded['updatedAt'], datetime)
            self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
            expected = {
                'name': name,
                'version': version,
                'vendor': vendor,
                'component': component,
                'updatedAt': uploaded['updatedAt'],
                'build': 1,
                'schema': '{"$schema": "http://json-schema.org/schema#"}',
                'hash': '180c4463f342b46548551cb463b6834363fa7e2d150f2bd4035190625b374602'
            }
            self.assertEqual(uploaded, expected)

            found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
            self.assertEqual(found, expected)

            found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})[
                'result']
            self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
            self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
            del found_history['builds'][0]['createdAt']
            self.assertEqual(found_history, {
                'name': name,
                'version': version,
                'vendor': vendor,
                'component': component,
                'builds': [
                    {
                        'createdBy': {
                            'group': self.claims['group'],
                            'username': self.claims['username']
                        },
                        'hash': '180c4463f342b46548551cb463b6834363fa7e2d150f2bd4035190625b374602',
                        'schema': '{"$schema": "http://json-schema.org/schema#"}',
                    }
                ]
            })

            self.assertRegex(str(e), "The new schema is not compatible with the old version "
                                     "that was already registered. Incompatible changes were")
        self.assertFalse(completed)

    @test_chainable
    def test_upsert_new_incompatible_override(self):
        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        self.rep.allow_override = True
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
            }
        }, self.claims)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
                '$schema': 'http://json-schema.org/schema#'
            }
        }, self.claims)

        uploaded = yield self.rep.find_latest(vendor, component, name, version)
        self.assertIsInstance(uploaded['updatedAt'], datetime)
        self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
        expected = {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'updatedAt': uploaded['updatedAt'],
            'build': 2,
            'schema': '{"$schema": "http://json-schema.org/schema#"}',
            'hash': '180c4463f342b46548551cb463b6834363fa7e2d150f2bd4035190625b374602'
        }
        self.assertEqual(uploaded, expected)

        found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
        self.assertEqual(found, expected)

        found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})[
            'result']
        self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
        self.assertIsInstance(found_history['builds'][1]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][1]['createdAt'], timedelta(seconds=1))
        del found_history['builds'][0]['createdAt']
        del found_history['builds'][1]['createdAt']
        self.maxDiff = None
        self.assertEqual(found_history, {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'builds': [
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'c89a148be40e6752261e3038609a4b68de22fa3bfdaf32f884edffb8480b9bbe',
                    'schema': '{}'
                },
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': '180c4463f342b46548551cb463b6834363fa7e2d150f2bd4035190625b374602',
                    'schema': '{"$schema": "http://json-schema.org/schema#"}'
                }
            ]
        })

    @test_chainable
    def test_upsert_new_incompatible3(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
                '$schema': 'http://json-schema.org/schema#draft-4'
            }
        }, self.claims)

        completed = False
        try:
            yield self.rep.upsert(vendor, component, {
                'name': name,
                'version': version,
                'schema': {
                    '$schema': 'http://json-schema.org/schema#'
                }
            }, self.claims)
        except SchemaException as e:
            uploaded = yield self.rep.find_latest(vendor, component, name, version)
            self.assertIsInstance(uploaded['updatedAt'], datetime)
            self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
            expected = {
                'name': name,
                'version': version,
                'vendor': vendor,
                'component': component,
                'updatedAt': uploaded['updatedAt'],
                'build': 1,
                'schema': '{"$schema": "http://json-schema.org/schema#draft-4"}',
                'hash': '4a8a0f916a35c4c3afd395692030eb3476b97e981ed1cfa80e66b9dbf60fcc23'
            }
            self.assertEqual(uploaded, expected)

            found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
            self.assertEqual(found, expected)

            found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})[
                'result']
            self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
            self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
            del found_history['builds'][0]['createdAt']
            self.assertEqual(found_history, {
                'name': name,
                'version': version,
                'vendor': vendor,
                'component': component,
                'builds': [
                    {
                        'createdBy': {
                            'group': self.claims['group'],
                            'username': self.claims['username']
                        },
                        'hash': '4a8a0f916a35c4c3afd395692030eb3476b97e981ed1cfa80e66b9dbf60fcc23',
                        'schema': '{"$schema": "http://json-schema.org/schema#draft-4"}',
                    }
                ]
            })

            self.assertRegex(str(e), "The new schema is not compatible with the old version that was "
                                     "already registered. Incompatible changes were")
        self.assertFalse(completed)

    @test_chainable
    def test_upsert_new_compatible(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
                'title': 'first title'
            }
        }, self.claims)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
                'title': 'second title'
            }
        }, self.claims)

        uploaded = yield self.rep.find_latest(vendor, component, name, version)
        self.assertIsInstance(uploaded['updatedAt'], datetime)
        self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
        expected = {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'updatedAt': uploaded['updatedAt'],
            'build': 2,
            'schema': '{"title": "second title"}',
            'hash': 'ac03e973037b7a48543a99ebfa6cbf2eecd86b0a26014fea510f7f743769977c'
        }
        self.assertEqual(uploaded, expected)

        found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
        self.assertEqual(found, expected)

        found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})[
            'result']
        self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
        self.assertIsInstance(found_history['builds'][1]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][1]['createdAt'], timedelta(seconds=1))
        del found_history['builds'][0]['createdAt']
        del found_history['builds'][1]['createdAt']
        self.maxDiff = None
        self.assertEqual(found_history, {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'builds': [
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'cae29d113f1ea59118a51a9bb3b52340bd494b166631a9f3cee998f1e2690ba7',
                    'schema': '{"title": "first title"}'
                },
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'ac03e973037b7a48543a99ebfa6cbf2eecd86b0a26014fea510f7f743769977c',
                    'schema': '{"title": "second title"}'
                }
            ]
        })

    @test_chainable
    def test_upsert_new_compatible_old(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
                'title': 'first title'
            }
        }, self.claims)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
                'title': 'second title'
            }
        }, self.claims)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
                'title': 'first title'
            }
        }, self.claims)

        uploaded = yield self.rep.find_latest(vendor, component, name, version)
        self.assertIsInstance(uploaded['updatedAt'], datetime)
        self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
        expected = {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'updatedAt': uploaded['updatedAt'],
            'build': 2,
            'schema': '{"title": "second title"}',
            'hash': 'ac03e973037b7a48543a99ebfa6cbf2eecd86b0a26014fea510f7f743769977c'
        }
        self.assertEqual(uploaded, expected)

        found = yield self.db.find_one('{}.schema'.format(self.type), {}, projection={'_id': False})['result']
        self.assertEqual(found, expected)

        found_history = yield self.db.find_one('{}.history'.format(self.type), {}, projection={'_id': False})[
            'result']
        self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
        self.assertIsInstance(found_history['builds'][1]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][1]['createdAt'], timedelta(seconds=1))
        del found_history['builds'][0]['createdAt']
        del found_history['builds'][1]['createdAt']
        self.maxDiff = None
        self.assertEqual(found_history, {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'builds': [
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'cae29d113f1ea59118a51a9bb3b52340bd494b166631a9f3cee998f1e2690ba7',
                    'schema': '{"title": "first title"}'
                },
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'ac03e973037b7a48543a99ebfa6cbf2eecd86b0a26014fea510f7f743769977c',
                    'schema': '{"title": "second title"}'
                }
            ]
        })

    @test_chainable
    def test_upsert_two_different(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        name2 = self.fake.word()
        version = self.fake.random_number(3)
        yield self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
                'title': 'first title'
            }
        }, self.claims)
        yield self.rep.upsert(vendor, component, {
            'name': name2,
            'version': version,
            'schema': {
                'title': 'second title'
            }
        }, self.claims)

        uploaded = yield self.rep.find_latest(vendor, component, name, version)
        self.assertIsInstance(uploaded['updatedAt'], datetime)
        self.assertLess(now() - uploaded['updatedAt'], timedelta(seconds=1))
        expected = {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'updatedAt': uploaded['updatedAt'],
            'build': 1,
            'schema': '{"title": "first title"}',
            'hash': 'cae29d113f1ea59118a51a9bb3b52340bd494b166631a9f3cee998f1e2690ba7'
        }
        self.assertEqual(uploaded, expected)

        self.maxDiff = None
        found = yield self.db.find_one('{}.schema'.format(self.type), {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component
        }, projection={'_id': False})['result']
        self.assertEqual(found, expected)

        found_history = yield self.db.find_one('{}.history'.format(self.type), {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component
        }, projection={'_id': False})['result']
        self.assertIsInstance(found_history['builds'][0]['createdAt'], datetime)
        self.assertLess(now() - found_history['builds'][0]['createdAt'], timedelta(seconds=1))
        del found_history['builds'][0]['createdAt']
        self.assertEqual(found_history, {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'builds': [
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'cae29d113f1ea59118a51a9bb3b52340bd494b166631a9f3cee998f1e2690ba7',
                    'schema': '{"title": "first title"}',
                }
            ]
        })

        uploaded2 = yield self.rep.find_latest(vendor, component, name2, version)
        self.assertIsInstance(uploaded2['updatedAt'], datetime)
        self.assertLess(now() - uploaded2['updatedAt'], timedelta(seconds=1))
        expected2 = {
            'name': name2,
            'version': version,
            'vendor': vendor,
            'component': component,
            'updatedAt': uploaded2['updatedAt'],
            'build': 1,
            'schema': '{"title": "second title"}',
            'hash': 'ac03e973037b7a48543a99ebfa6cbf2eecd86b0a26014fea510f7f743769977c'
        }
        self.assertEqual(uploaded2, expected2)

        found2 = yield self.db.find_one('{}.schema'.format(self.type), {
            'name': name2,
            'version': version,
            'vendor': vendor,
            'component': component
        }, projection={'_id': False})['result']
        self.assertEqual(found2, expected2)

        found_history2 = yield self.db.find_one('{}.history'.format(self.type), {
            'name': name2,
            'version': version,
            'vendor': vendor,
            'component': component
        }, projection={'_id': False})['result']
        self.assertIsInstance(found_history2['builds'][0]['createdAt'], datetime)
        self.assertLess(now() - found_history2['builds'][0]['createdAt'], timedelta(seconds=1))
        del found_history2['builds'][0]['createdAt']
        self.assertEqual(found_history2, {
            'name': name2,
            'version': version,
            'vendor': vendor,
            'component': component,
            'builds': [
                {
                    'createdBy': {
                        'group': self.claims['group'],
                        'username': self.claims['username']
                    },
                    'hash': 'ac03e973037b7a48543a99ebfa6cbf2eecd86b0a26014fea510f7f743769977c',
                    'schema': '{"title": "second title"}',
                }
            ]
        })

    @test_chainable
    def test_get_non_existing(self):
        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        uploaded = yield self.rep.find_latest(vendor, component, name, version)
        self.assertEqual(uploaded, None)

    def test_ignored_keywords(self):
        self.assertEqual(self.rep.ignored_keywords, ['title', 'description', 'examples'])

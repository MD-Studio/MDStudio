from datetime import datetime
from faker import Faker
from twisted.internet import reactor

from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from lie_schema import SchemaWampApi

from lie_schema.schema_repository import SchemaRepository
from mdstudio.deferred.chainable import chainable
from mdstudio.unittest import wait_for_completion
from mdstudio.unittest.db import DBTestCase


class TestSchemaRepository(DBTestCase):
    fake = Faker()

    def setUp(self):

        self.service = SchemaWampApi()
        self.type = self.fake.word()
        self.db = MongoClientWrapper("localhost", 27127).get_database('users~schemaTest')
        self.rep = SchemaRepository(self.service, self.type, self.db)
        self.claims = {
            'username': self.fake.user_name(),
            'group': self.fake.user_name()
        }

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

        wait_for_completion.wait_for_completion = True

    def tearDown(self):
        wait_for_completion.wait_for_completion = False

    def test_construction(self):
        self.assertEqual(self.service, self.rep.session)
        self.assertEqual(self.type, self.rep.type)

    @chainable
    def test_upsert(self):

        vendor = self.fake.word()
        component = self.fake.word()
        name = self.fake.word()
        version = self.fake.random_number(3)
        self.rep.upsert(vendor, component, {
            'name': name,
            'version': version,
            'schema': {
            }
        }, self.claims)

        uploaded = yield self.rep.find_latest(vendor, component, name, version)
        self.assertIsInstance(uploaded['updatedAt'], datetime)
        self.assertEqual(uploaded, {
            'name': name,
            'version': version,
            'vendor': vendor,
            'component': component,
            'build': 1,
            'schema': '{}',
            'hash': self.rep.hash_schema({

            })
        })
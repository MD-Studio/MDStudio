from faker import Faker
from twisted.internet import reactor

from lie_db.application import DBComponent
from lie_db.key_repository import KeyRepository
from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from mdstudio.unittest.db import DBTestCase


class TestKeyRepository(DBTestCase):

    fake = Faker()

    def setUp(self):

        self.service = DBComponent()
        self.service.component_config.settings['secret'] = "secret password"
        self.service._set_secret()
        self.db = MongoClientWrapper("localhost", 27127).get_database('users~db')
        self.rep = KeyRepository(self.service, self.db)
        self.claims = {
            'username': self.fake.user_name(),
            'group': self.fake.user_name()
        }

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

    def test_construction(self):
        self.assertEqual(self.service, self.rep._session)
        self.assertEqual(self.db, self.rep._internal_db)

    def test_get_key(self):
        claim = {
            'connectionType': 'user',
            'username': 'test-user'
        }

        key = self.rep.get_key(claim)
        self.assertEqual(key,  self.rep.get_key(claim))

        self.service.component_config.settings['secret'] = "new secret"
        self.service._set_secret()
        self.assertNotEqual(key,  self.rep.get_key(claim))
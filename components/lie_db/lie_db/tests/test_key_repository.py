from cryptography.fernet import Fernet
from faker import Faker
from twisted.internet import reactor

from lie_db.application import DBComponent
from lie_db.key_repository import KeyRepository
from mdstudio.db.exception import DatabaseException
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

    def test_get_key_update(self):
        claim = {
            'connectionType': 'user',
            'username': 'test-user'
        }

        key = self.rep.get_key(claim)
        self.assertEqual(key,  self.rep.get_key(claim))

        self.service.component_config.settings['secret'] = "new secret"
        self.service._set_secret()
        self.assertRaisesRegex(DatabaseException, "Tried to decrypt the component key with a different secret!"
                                                  " Please use your old secret.", self.rep.get_key, claim)

    def test_get_key_differs(self):
        claim = {
            'connectionType': 'user',
            'username': 'test-user'
        }
        claim2 = {
            'connectionType': 'user',
            'username': 'test-user2'
        }
        self.assertEqual(self.rep.get_key(claim),  self.rep.get_key(claim))
        self.assertEqual(self.rep.get_key(claim2),  self.rep.get_key(claim2))
        self.assertNotEqual(self.rep.get_key(claim),  self.rep.get_key(claim2))

    def test_get_key_differs2(self):
        claim = {
            'connectionType': 'group',
            'group': 'test-group'
        }
        claim2 = {
            'connectionType': 'group',
            'group': 'test-group2'
        }
        self.assertEqual(self.rep.get_key(claim),  self.rep.get_key(claim))
        self.assertEqual(self.rep.get_key(claim2),  self.rep.get_key(claim2))
        self.assertNotEqual(self.rep.get_key(claim),  self.rep.get_key(claim2))

    def test_get_key_differs3(self):
        claim = {
            'connectionType': 'groupRole',
            'group': 'test-group',
            'groupRole': 'test-groupRole'
        }
        claim2 = {
            'connectionType': 'groupRole',
            'group': 'test-group2',
            'groupRole': 'test-groupRole'
        }
        self.assertEqual(self.rep.get_key(claim),  self.rep.get_key(claim))
        self.assertEqual(self.rep.get_key(claim2),  self.rep.get_key(claim2))
        self.assertNotEqual(self.rep.get_key(claim),  self.rep.get_key(claim2))

    def test_get_key_differs4(self):
        claim = {
            'connectionType': 'groupRole',
            'group': 'test-group',
            'groupRole': 'test-groupRole'
        }
        claim2 = {
            'connectionType': 'groupRole',
            'group': 'test-group',
            'groupRole': 'test-groupRole2'
        }
        self.assertEqual(self.rep.get_key(claim),  self.rep.get_key(claim))
        self.assertEqual(self.rep.get_key(claim2),  self.rep.get_key(claim2))
        self.assertNotEqual(self.rep.get_key(claim),  self.rep.get_key(claim2))
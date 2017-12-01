from faker import Faker
from twisted.internet import reactor

from lie_db.application import DBComponent
from lie_db.key_repository import KeyRepository
from mdstudio.db.exception import DatabaseException
from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from mdstudio.deferred.chainable import test_chainable
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
        self.assertEqual(key, self.rep.get_key(claim))

    def test_decrypt_key_fixed(self):
        self.assertEqual(
            self.rep._decrypt_key(b'gAAAAABaHIEz5dSxp5hCh4i9-hCTjjmCnGJXlknw1Wb4BMzjOejud0fXoP55tOO1Lay6bLOq6s-NfudK7lJSrH7KccKzgX0EQQ=='),
            b'test')

    @test_chainable
    def test_get_key_fixed(self):
        claim = {
            'connectionType': 'user',
            'username': 'test-user'
        }

        yield self.db.insert_many('user.keys', [
            {
                'type': 'user',
                'username': 'test-user',
                'key': b'gAAAAABaHH46aBa9mmSeil9ySZ2KXJyvS5MjvZcN_pF2-3tAuS9k9ljyDmhTWUAvN0D33WkoJRWtcE4fTe5mMqjFaVshFChexbfJ7kPQ3KRR19Ho3LPjT1lJrdhiBIttpu0ic6GHfSUX'
            }
        ])
        key = self.rep.get_key(claim)
        self.assertEqual(key, b'9EA6E072aFKxdZ1GkCR_pYc0M5ELouDs9d1fm2bYoMw=')

    @test_chainable
    def test_get_key_fixed2(self):
        claim = {
            'connectionType': 'group',
            'group': 'test-group'
        }

        yield self.db.insert_many('group.keys', [
            {
                'type': 'group',
                'group': 'test-group',
                'key': b'gAAAAABaHH7egLiGGIGJ6Z0wCJi7-r2vOQr_oHy3A_rKkTTkIxSQzfvze1GHCvWcagskLxM8fWWg21QbL6N_E6uE9NmDHcgCb3axbGfSHcfqZ9f4TeQgGNZ-l9SG8_vWsDin4LX9JALu'
            }
        ])

        key = self.rep.get_key(claim)
        self.assertEqual(key, b'-cx1mKYdvY604rsE41iEgVqtOzOaaULGV9ANTqUjxpE=')

    @test_chainable
    def test_get_key_fixed3(self):
        claim = {
            'connectionType': 'groupRole',
            'group': 'test-group',
            'groupRole': 'test-groupRole'
        }

        yield self.db.insert_many('groupRole.keys', [
            {
                'type': 'groupRole',
                'group': 'test-group',
                'groupRole': 'test-groupRole',
                'key': b'gAAAAABaHH9gLYfFcNwQ6A_wQNH9x94l4s239NG4pnwyf2-T3UQpkflMg_9bXIEeKSANDd3YWH1S5y_N4fA_Je8f43e5xAzwAvCE058x57lf7z9QI4ersiuQ8S08xjRv2kx8TUNzkWPP'
            }
        ])

        key = self.rep.get_key(claim)
        self.assertEqual(key, b'QGpvJnz-skkMHtlpB5eR2-7LLQFqhlG89sMjuF1oRbE=')

    def test_get_key_update(self):
        claim = {
            'connectionType': 'user',
            'username': 'test-user'
        }

        key = self.rep.get_key(claim)
        self.assertEqual(key, self.rep.get_key(claim))

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
        self.assertEqual(self.rep.get_key(claim), self.rep.get_key(claim))
        self.assertEqual(self.rep.get_key(claim2), self.rep.get_key(claim2))
        self.assertNotEqual(self.rep.get_key(claim), self.rep.get_key(claim2))

    def test_get_key_differs2(self):
        claim = {
            'connectionType': 'group',
            'group': 'test-group'
        }
        claim2 = {
            'connectionType': 'group',
            'group': 'test-group2'
        }
        self.assertEqual(self.rep.get_key(claim), self.rep.get_key(claim))
        self.assertEqual(self.rep.get_key(claim2), self.rep.get_key(claim2))
        self.assertNotEqual(self.rep.get_key(claim), self.rep.get_key(claim2))

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
        self.assertEqual(self.rep.get_key(claim), self.rep.get_key(claim))
        self.assertEqual(self.rep.get_key(claim2), self.rep.get_key(claim2))
        self.assertNotEqual(self.rep.get_key(claim), self.rep.get_key(claim2))

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
        self.assertEqual(self.rep.get_key(claim), self.rep.get_key(claim))
        self.assertEqual(self.rep.get_key(claim2), self.rep.get_key(claim2))
        self.assertNotEqual(self.rep.get_key(claim), self.rep.get_key(claim2))

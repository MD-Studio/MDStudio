from faker import Faker
from mock import mock

from lie_db import DBWampApi
from mdstudio.db.connection import ConnectionType
from mdstudio.deferred.chainable import chainable
from mdstudio.unittest.api import APITestCase
from mdstudio.unittest.db import DBTestCase


class TestWampServiceAuthorize(DBTestCase, APITestCase):
    def setUp(self):
        self.service = DBWampApi()
        self.service._client.get_database = mock.MagicMock(wraps=lambda x: x)
        self.fake = Faker()
        self.fake.seed(4321)

    @chainable
    def test_get_database_user(self):

        for i in range(50):
            self.service._client.get_database.reset_mock()
            username = self.fake.simple_profile()['username']
            db = yield self.service.get_database({
                'username': username,
                'connectionType': str(ConnectionType.User)
            })
            self.service._client.get_database.assert_called_once_with('users~{}'.format(username))
            self.assertEqual(db, 'users~{}'.format(username))

    @chainable
    def test_get_database_group(self):

        for i in range(50):
            self.service._client.get_database.reset_mock()
            group = self.fake.slug()
            db = yield self.service.get_database({
                'connectionType': str(ConnectionType.Group),
                'group': group
            })
            self.service._client.get_database.assert_called_once_with('groups~{}'.format(group))
            self.assertEqual(db, 'groups~{}'.format(group))

    @chainable
    def test_get_database_group_role(self):

        for i in range(50):
            self.service._client.get_database.reset_mock()
            group = self.fake.slug()
            group_role = self.fake.slug()
            db = yield self.service.get_database({
                'connectionType': str(ConnectionType.GroupRole),
                'group': group,
                'groupRole': group_role
            })
            self.service._client.get_database.assert_called_once_with('grouproles~{}~{}'.format(group, group_role))
            self.assertEqual(db, 'grouproles~{}~{}'.format(group, group_role))

    def test_get_database_other(self):

        db = self.service.get_database({
            'connectionType':  self.fake.slug()
        })
        self.assertFailure(db, ValueError)

        return db
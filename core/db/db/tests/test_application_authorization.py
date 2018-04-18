from faker import Faker
from mdstudio.unittest.settings import load_settings
from mock import mock

from db.application import DBComponent
from mdstudio.db.connection_type import ConnectionType
from mdstudio.deferred.chainable import test_chainable
from mdstudio.unittest.api import APITestCase
from mdstudio.unittest.db import DBTestCase


class TesDBComponentAuthorize(DBTestCase, APITestCase):
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
        self.service._client.get_database = mock.MagicMock(wraps=lambda x: x)

    @test_chainable
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

    @test_chainable
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

    @test_chainable
    def test_get_database_group_role(self):

        for i in range(50):
            self.service._client.get_database.reset_mock()
            group = self.fake.slug()
            group_role = self.fake.slug()
            db = yield self.service.get_database({
                'connectionType': str(ConnectionType.GroupRole),
                'group': group,
                'role': group_role
            })
            self.service._client.get_database.assert_called_once_with('grouproles~{}~{}'.format(group, group_role))
            self.assertEqual(db, 'grouproles~{}~{}'.format(group, group_role))

    @test_chainable
    def test_get_database_other(self):

        db = self.service.get_database({
            'connectionType': self.fake.slug()
        })
        yield self.assertFailure(db, ValueError)

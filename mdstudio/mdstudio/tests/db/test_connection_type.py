# coding=utf-8
import unittest

from mdstudio.db.connection_type import ConnectionType


class ConnectionTypeTests(unittest.TestCase):
    def test_user(self):
        self.assertEqual(str(ConnectionType.User), 'user')

    def test_group(self):
        self.assertEqual(str(ConnectionType.Group), 'group')

    def test_group_role(self):
        self.assertEqual(str(ConnectionType.GroupRole), 'groupRole')

    def test_user2(self):
        self.assertEqual(int(ConnectionType.User), 0)

    def test_group2(self):
        self.assertEqual(int(ConnectionType.Group), 1)

    def test_group_role_2(self):
        self.assertEqual(int(ConnectionType.GroupRole), 2)

    def test_neq(self):
        self.assertNotEqual(ConnectionType.User, ConnectionType.Group)
        self.assertNotEqual(ConnectionType.User, ConnectionType.GroupRole)
        self.assertNotEqual(ConnectionType.GroupRole, ConnectionType.Group)

    def test_user_from_string(self):
        self.assertEqual(ConnectionType.from_string('user'), ConnectionType.User)

    def test_group_from_string(self):
        self.assertEqual(ConnectionType.from_string('group'), ConnectionType.Group)

    def test_group_role_from_string(self):
        self.assertEqual(ConnectionType.from_string('groupRole'), ConnectionType.GroupRole)

    def test_other_from_string(self):
        self.assertRaises(ValueError, ConnectionType.from_string, 'wefwef')

# coding=utf-8
import unittest

from mdstudio.logging.log_type import LogType


class LogTypeTests(unittest.TestCase):
    def test_user(self):
        self.assertEqual(str(LogType.User), 'user')

    def test_group(self):
        self.assertEqual(str(LogType.Group), 'group')

    def test_group_role(self):
        self.assertEqual(str(LogType.GroupRole), 'groupRole')

    def test_user2(self):
        self.assertEqual(int(LogType.User), 0)

    def test_group2(self):
        self.assertEqual(int(LogType.Group), 1)

    def test_group_role_2(self):
        self.assertEqual(int(LogType.GroupRole), 2)

    def test_neq(self):
        self.assertNotEqual(LogType.User, LogType.Group)
        self.assertNotEqual(LogType.User, LogType.GroupRole)
        self.assertNotEqual(LogType.GroupRole, LogType.Group)

    def test_user_from_string(self):
        self.assertEqual(LogType.from_string('user'), LogType.User)

    def test_group_from_string(self):
        self.assertEqual(LogType.from_string('group'), LogType.Group)

    def test_group_role_from_string(self):
        self.assertEqual(LogType.from_string('groupRole'), LogType.GroupRole)

    def test_other_from_string(self):
        self.assertRaises(ValueError, LogType.from_string, 'wefwef')
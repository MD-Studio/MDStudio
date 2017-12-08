from unittest import TestCase

from mdstudio.session import GlobalSession


class GlobalSessionTest(TestCase):

    def test_construction(self):
        connection = GlobalSession({'test': {'testobject'}})

        self.assertEqual(connection._session, {'test': {'testobject'}})
        self.assertIs(connection, GlobalSession())

# coding=utf-8
import unittest
import mock
from autobahn.twisted import ApplicationSession

from mdstudio.db.model import Model
from mdstudio.db.session_database import SessionDatabaseWrapper


class ModelTests(unittest.TestCase):

    def setUp(self):
        self.wrapper = mock.MagicMock(spec=ApplicationSession)
        self.wrapper.component_info = mock.MagicMock()
        self.wrapper.component_info.get = mock.MagicMock(return_value='namespace')
        self.wrapper.call = mock.MagicMock(return_value='namespace')
        self.collection = 'coll'
        self.model = Model(self.wrapper, self.collection)

    def test_construction(self):

        self.wrapper = mock.Mock()
        self.collection = 'coll'
        self.model = Model(self.wrapper, self.collection)
        self.assertEqual(self.model.wrapper, self.wrapper)

    def test_construction2(self):

        self.assertNotEquals(self.model.wrapper, self.wrapper)

        self.assertIsInstance(self.model.wrapper, SessionDatabaseWrapper)

    def test_construction_class(self):

        class Users(Model):
            pass

        self.model = Users(self.wrapper)

        self.assertEquals(self.model.collection, "users")
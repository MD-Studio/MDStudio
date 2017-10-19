# coding=utf-8
import twisted

from lie_db.db_methods import MongoDatabaseWrapper
from lie_db.mongo_client_wrapper import MongoClientWrapper
from mdstudio.db.model import Model
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.unittest.mongo import TrialDBTestCase

twisted.internet.base.DelayedCall.debug = True
class TestMongoDatabaseWrapper(TrialDBTestCase):

    def setUp(self):
        self.db = MongoClientWrapper("localhost", 27127).get_namespace('testns')
        self.d = Model(self.db, 'test_collection')

    @chainable
    def test_insert_one(self):
        id = yield self.d.insert_one({'test': 2, '_id': 80})
        print(id)
        self.assertEqual(id, 80)
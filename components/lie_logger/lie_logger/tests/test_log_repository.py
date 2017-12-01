from datetime import timedelta
from pprint import pprint

from faker import Faker
from twisted.internet import reactor

from lie_logger.application import LoggerComponent
from lie_logger.log_repository import LogRepository
from mdstudio.db.impl.mongo_client_wrapper import MongoClientWrapper
from mdstudio.deferred.chainable import test_chainable
from mdstudio.unittest.db import DBTestCase
from mdstudio.utc import from_utc_string, now


class TestLogRepository(DBTestCase):
    faker = Faker()

    def setUp(self):
        self.service = LoggerComponent()
        self.db = MongoClientWrapper("localhost", 27127).get_database('users~db')
        self.rep = LogRepository(self.db)
        self.claims = {
            'logType': 'user',
            'username': self.faker.user_name(),
            'group': self.faker.user_name()
        }

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

    def test_construction(self):
        self.assertEqual(self.db, self.rep.db)

    def test_get_log_collection_name(self):
        self.assertEqual(LogRepository.get_log_collection_name({
            'logType': 'user',
            'username': 'test-user'
        }), 'users~test-user')

    def test_get_log_collection_name2(self):
        self.assertEqual(LogRepository.get_log_collection_name({
            'logType': 'group',
            'group': 'test-group'
        }), 'groups~test-group')

    def test_get_log_collection_name3(self):
        self.assertEqual(LogRepository.get_log_collection_name({
            'logType': 'groupRole',
            'group': 'test-group',
            'groupRole': 'test-group-role'
        }), 'grouproles~test-group~test-group-role')

    def test_get_log_collection_name_not_exists(self):
        self.assertRaises(ValueError, LogRepository.get_log_collection_name, {
            'logType': 'random',
            'group': 'test-group',
            'groupRole': 'test-group-role'
        })

    def test_logs(self):
        self.assertEqual(self.rep.logs({
            'logType': 'user',
            'username': 'test-user'
        }).collection, 'users~test-user')

    def test_logs2(self):
        self.assertEqual(self.rep.logs({
            'logType': 'group',
            'group': 'test-group'
        }).collection, 'groups~test-group')

    def test_logs3(self):
        self.assertEqual(self.rep.logs({
            'logType': 'groupRole',
            'group': 'test-group',
            'groupRole': 'test-group-role'
        }).collection, 'grouproles~test-group~test-group-role')

    def test_logs_not_exists(self):
        self.assertRaises(ValueError, self.rep.logs, {
            'logType': 'random',
            'group': 'test-group',
            'groupRole': 'test-group-role'
        })

    @test_chainable
    def test_insert(self):
        dic1 = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
        dic2 = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
        yield self.rep.insert(self.claims, [dic1, dic2])
        all = yield self.db.find_many('users~{}'.format(self.claims['username']), {}, projection={'_id': False})['results']

        self.assertLessEqual(now() - all[0]['createdAt'], timedelta(seconds=1))
        del all[0]['createdAt']
        dic1['createdBy'] = self.claims
        self.assertEqual(all[0], dic1)

        self.assertLessEqual(now() - all[1]['createdAt'], timedelta(seconds=1))
        del all[1]['createdAt']
        dic2['createdBy'] = self.claims
        self.assertEqual(all[1], dic2)
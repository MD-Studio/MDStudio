from faker import Faker
from mock import mock, call
from twisted.internet import reactor

from lie_logger.application import LoggerComponent
from lie_logger.log_repository import LogRepository
from mdstudio.api.api_result import APIResult
from mdstudio.api.exception import CallException
from mdstudio.deferred.chainable import test_chainable
from mdstudio.unittest.api import APITestCase
from mdstudio.unittest.db import DBTestCase


class TestLoggerComponent(DBTestCase, APITestCase):
    faker = Faker()

    def setUp(self):
        self.service = LoggerComponent()
        self.vendor = self.faker.word()
        self.username = self.faker.word()
        self.claims = {
            'logType': 'user',
            'username': self.faker.user_name(),
            'group': self.faker.user_name()
        }

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

    def test_pre_init(self):
        self.service.component_waiters = mock.MagicMock()
        self.service.component_waiters.append = mock.MagicMock()
        self.service.pre_init()
        self.assertIsInstance(self.service.logs, LogRepository)
        self.service.component_waiters.append.assert_has_calls([
            call(self.service.db_waiter),
            call(self.service.schema_waiter),
        ])

    @mock.patch("mdstudio.component.impl.core.CoreComponentSession.on_run")
    @test_chainable
    def test_on_run(self, m):

        self.service.call = mock.MagicMock()
        yield self.service.on_run()
        self.service.call.assert_has_calls([
            call('mdstudio.auth.endpoint.ring0.set-status', {'status': True})
        ])
        m.assert_called_once()

    @test_chainable
    def test_push_logs(self):

        self.service.logs.insert = mock.MagicMock(wraps=lambda c, r: r)
        dic1 = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
        dic2 = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')

        dic1['level'] = 'info'
        dic2['level'] = 'warn'

        output = yield self.assertApi(self.service, 'push_logs', {
            'logs': [dic1, dic2]
        }, self.claims)
        self.assertEqual(output, 2)
        self.service.logs.insert.assert_has_calls([
            call(self.claims, [dic1, dic2])
        ])

    @test_chainable
    def test_push_logs_error(self):
        def raise_(ex):
            raise ex

        self.service.logs.insert = mock.MagicMock(wraps=lambda c, r: raise_(CallException))
        dic1 = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
        dic2 = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')

        dic1['level'] = 'info'
        dic2['level'] = 'warn'

        output = yield self.assertApi(self.service, 'push_logs', {
            'logs': [dic1, dic2]
        }, self.claims)
        self.assertIsInstance(output, APIResult)
        self.assertEqual(output.error, 'The database is not online, please try again later.')

    @test_chainable
    def test_push_event(self):

        self.service.logs.insert = mock.MagicMock(wraps=lambda c, r, tags: r)
        dic1 = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')

        dic1['level'] = 'info'
        tags = self.faker.pylist(10, True, 'str')
        dic1['tags'] =tags

        output = yield self.assertApi(self.service, 'push_event', {
            'event': dic1
        }, self.claims)
        self.assertEqual(output, 1)
        self.service.logs.insert.assert_has_calls([
            call(self.claims, [dic1], tags)
        ])

    @test_chainable
    def test_push_event_error(self):
        def raise_(ex):
            raise ex

        self.service.logs.insert = mock.MagicMock(wraps=lambda c, r, tags: raise_(CallException))
        dic1 = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')

        dic1['level'] = 'info'
        dic1['tags'] = self.faker.pylist(10, True, 'str')

        output = yield self.assertApi(self.service, 'push_event', {
            'event': dic1
        }, self.claims)
        self.assertIsInstance(output, APIResult)
        self.assertEqual(output.error, 'The database is not online, please try again later.')
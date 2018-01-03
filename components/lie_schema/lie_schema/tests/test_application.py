import json

from faker import Faker
from mock import mock, call
from twisted.internet import reactor

from lie_schema.application import SchemaComponent
from lie_schema.exception import SchemaException
from lie_schema.schema_repository import SchemaRepository
from mdstudio.deferred.chainable import chainable, test_chainable
from mdstudio.unittest.api import APITestCase
from mdstudio.unittest.db import DBTestCase


class TestSchemaComponent(DBTestCase, APITestCase):
    faker = Faker()

    def setUp(self):
        self.service = SchemaComponent()
        self.vendor = self.faker.word()
        self.username = self.faker.word()
        self.claims = {
            'vendor': self.vendor,
            'username': self.username
        }

        if not reactor.getThreadPool().started:
            reactor.getThreadPool().start()

    def test_pre_init(self):

        self.service.pre_init()
        self.assertIsInstance(self.service.endpoints, SchemaRepository)
        self.assertIsInstance(self.service.resources, SchemaRepository)
        self.assertIsInstance(self.service.claims, SchemaRepository)

    @mock.patch("mdstudio.component.impl.core.CoreComponentSession.on_run")
    @test_chainable
    def test_on_run(self, m):

        self.service.call = mock.MagicMock()
        yield self.service.on_run()
        self.service.call.assert_has_calls([
            call('mdstudio.auth.endpoint.ring0.set-status', {'status': True})
        ])
        m.assert_called_once()

    @chainable
    def test_upload_endpoints(self):

        self.service.endpoints = mock.MagicMock()
        for _ in range(50):
            self.service.endpoints.upsert = mock.MagicMock()

            obj = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            obj['component'] = self.faker.word()
            obj['schemas'] = {
                'endpoints': [
                    {
                        'order': 'first'
                    }
                ]
            }
            yield self.assertApi(self.service, 'schema_upload', obj, self.claims)

            self.service.endpoints.upsert.assert_called_once_with(self.vendor, obj['component'], {'order': 'first'}, self.claims)

    @chainable
    def test_upload_endpoints_multiple(self):

        self.service.endpoints = mock.MagicMock()
        for i in range(50):
            self.service.endpoints.upsert = mock.MagicMock()

            obj = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            obj['component'] = self.faker.word()
            obj['schemas'] = {
                'endpoints': [
                    {
                        'order': i
                    },
                    {
                        'order': i * 2
                    }
                ]
            }
            yield self.assertApi(self.service, 'schema_upload', obj, self.claims)

            self.service.endpoints.upsert.assert_has_calls([
                call(self.vendor, obj['component'], {'order': i}, self.claims),
                call(self.vendor, obj['component'], {'order': i * 2}, self.claims)
            ])

    @chainable
    def test_upload_resource(self):

        self.service.resources = mock.MagicMock()
        for _ in range(50):
            self.service.resources.upsert = mock.MagicMock()

            obj = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            obj['component'] = self.faker.word()
            obj['schemas'] = {
                'resources': [
                    {
                        'order': 'first'
                    }
                ]
            }
            yield self.assertApi(self.service, 'schema_upload', obj, self.claims)

            self.service.resources.upsert.assert_called_once_with(self.vendor, obj['component'], {'order': 'first'}, self.claims)

    @chainable
    def test_upload_resource_multiple(self):

        self.service.resources = mock.MagicMock()
        for i in range(50):
            self.service.resources.upsert = mock.MagicMock()

            obj = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            obj['component'] = self.faker.word()
            obj['schemas'] = {
                'resources': [
                    {
                        'order': i
                    },
                    {
                        'order': i * 2
                    }
                ]
            }
            yield self.assertApi(self.service, 'schema_upload', obj, self.claims)

            self.service.resources.upsert.assert_has_calls([
                call(self.vendor, obj['component'], {'order': i}, self.claims),
                call(self.vendor, obj['component'], {'order': i * 2}, self.claims)
            ])

    @chainable
    def test_upload_claim(self):

        self.service.claims = mock.MagicMock()
        for _ in range(50):
            self.service.claims.upsert = mock.MagicMock()

            obj = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            obj['component'] = self.faker.word()
            obj['schemas'] = {
                'claims': [
                    {
                        'order': 'first'
                    }
                ]
            }
            yield self.assertApi(self.service, 'schema_upload', obj, self.claims)

            self.service.claims.upsert.assert_called_once_with(self.vendor, obj['component'], {'order': 'first'}, self.claims)

    @chainable
    def test_upload_claim_multiple(self):

        self.service.claims = mock.MagicMock()
        for i in range(50):
            self.service.claims.upsert = mock.MagicMock()

            obj = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            obj['component'] = self.faker.word()
            obj['schemas'] = {
                'claims': [
                    {
                        'order': i
                    },
                    {
                        'order': i * 2
                    }
                ]
            }
            yield self.assertApi(self.service, 'schema_upload', obj, self.claims)

            self.service.claims.upsert.assert_has_calls([
                call(self.vendor, obj['component'], {'order': i}, self.claims),
                call(self.vendor, obj['component'], {'order': i * 2}, self.claims)
            ])

    @chainable
    def test_get_endpoint(self):

        self.service.claims = mock.MagicMock()
        for _ in range(50):
            self.service.endpoints.find_latest = mock.MagicMock(return_value={'schema': json.dumps({'test': 'schema'})})
            component = self.faker.word()
            name = self.faker.word()
            version = self.faker.random_number(3)
            obj = {
                'component': component,
                'type': 'endpoint',
                'name': name,
                'version': version
            }
            output = yield self.assertApi(self.service, 'schema_get', obj, self.claims)
            self.assertEqual(output, {'test': 'schema'})
            self.service.endpoints.find_latest.assert_called_once_with(self.vendor, component, name, version)

    @chainable
    def test_get_resource(self):

        self.service.claims = mock.MagicMock()
        for _ in range(50):
            self.service.resources.find_latest = mock.MagicMock(return_value={'schema': json.dumps({'test': 'schema'})})
            component = self.faker.word()
            name = self.faker.word()
            version = self.faker.random_number(3)
            obj = {
                'component': component,
                'type': 'resource',
                'name': name,
                'version': version
            }
            output = yield self.assertApi(self.service, 'schema_get', obj, self.claims)
            self.assertEqual(output, {'test': 'schema'})
            self.service.resources.find_latest.assert_called_once_with(self.vendor, component, name, version)

    @chainable
    def test_get_claim(self):

        self.service.claims = mock.MagicMock()
        for _ in range(50):
            self.service.claims.find_latest = mock.MagicMock(return_value={'schema': json.dumps({'test': 'schema'})})
            component = self.faker.word()
            name = self.faker.word()
            version = self.faker.random_number(3)
            obj = {
                'component': component,
                'type': 'claim',
                'name': name,
                'version': version
            }
            output = yield self.assertApi(self.service, 'schema_get', obj, self.claims)
            self.assertEqual(output, {'test': 'schema'})
            self.service.claims.find_latest.assert_called_once_with(self.vendor, component, name, version)

    @chainable
    def test_get_other(self):

        self.service.claims = mock.MagicMock()
        for _ in range(50):
            self.service.claims.find_latest = mock.MagicMock(return_value={'schema': json.dumps({'test': 'schema'})})
            component = self.faker.word()
            name = self.faker.word()
            type = self.faker.word()
            version = self.faker.random_number(3)
            obj = {
                'component': component,
                'type': type,
                'name': name,
                'version': version
            }
            completed = False

            try:
                yield self.assertApi(self.service, 'schema_get', obj, self.claims)
                completed = True
            except SchemaException as e:
                self.assertRegex(str(e), 'Schema type "{}" is not known'.format(type))
            self.assertFalse(completed)

    @chainable
    def test_get_not_found(self):

        self.service.claims = mock.MagicMock()
        for _ in range(50):
            self.service.claims.find_latest = mock.MagicMock(return_value=None)
            component = self.faker.word()
            name = self.faker.word()
            version = self.faker.random_number(3)
            obj = {
                'component': component,
                'type': 'claim',
                'name': name,
                'version': version
            }
            completed = False

            try:
                yield self.assertApi(self.service, 'schema_get', obj, self.claims)
                completed = True
            except SchemaException as e:
                self.assertRegex(str(e),
                                 'Schema name "{}" with type "{}", and version "{}" on "{}/{}" was not found'.format(name, 'claim', version,
                                                                                                                     self.vendor,
                                                                                                                     component))
            self.assertFalse(completed)

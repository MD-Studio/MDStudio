import json

import os
from faker import Faker
from jsonschema import ValidationError
from mock import mock

from mdstudio.api.exception import RegisterException
from mdstudio.deferred.chainable import test_chainable

from mdstudio.unittest.db import DBTestCase
from pyfakefs.fake_filesystem_unittest import Patcher, TestCase

from mdstudio.api.schema import ISchema, ResourceSchema, EndpointSchema, HttpsSchema, InlineSchema, ClaimSchema, validate_json_schema, \
    MDStudioClaimSchema


class ISchemaTests(DBTestCase):
    faker = Faker()

    def test_construction(self):
        schema = ISchema()
        self.assertEqual(schema.cached, {})

    def test_retrieve_local(self):
        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path()
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.json', contents=json.dumps(content))

                schema = ISchema()
                schema._retrieve_local(base_path, schema_path)
                self.assertEqual(schema.cached, {
                    1: content
                })

    def test_retrieve_local_not_exists(self):
        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path()

                schema = ISchema()
                self.assertRaises(FileNotFoundError, schema._retrieve_local, base_path, schema_path)

    def test_retrieve_local_version(self):
        for i in range(50):
            with Patcher() as patcher:

                base_path = self.faker.file_path()
                schema_path = self.faker.file_path()
                versions = {self.faker.random_number(3) for i in range(self.faker.random_number(2))}
                versions.add(self.faker.random_number(3))
                contents = {}
                for v in versions:
                    content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                    patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v{}.json'.format(v), contents=json.dumps(content))
                    contents[v] = content

                schema = ISchema()
                schema._retrieve_local(base_path, schema_path, versions=versions)
                self.assertEqual(schema.cached, contents)

    def test_retrieve_local_version_single(self):
        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path()
                version = self.faker.random_number(3)
                contents = {}
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v{}.json'.format(version), contents=json.dumps(content))
                contents[version] = content

                schema = ISchema()
                schema._retrieve_local(base_path, schema_path, versions=version)
                self.assertEqual(schema.cached, contents)

    def test_retrieve_local_version_single0(self):
        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path()
                version = 0
                contents = {}
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v{}.json'.format(version), contents=json.dumps(content))
                contents[version] = content

                schema = ISchema()
                schema._retrieve_local(base_path, schema_path, versions=version)
                self.assertEqual(schema.cached, contents)

    @test_chainable
    def test_recurse_subschemas_no_refs(self):

        for i in range(50):
            content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            schema = ISchema()
            out = yield schema._recurse_subschemas(content, None)
            self.assertEqual(schema.cached, {})
            self.assertEqual(out, {
                'schema': content,
                'success': True
            })

    @test_chainable
    def test_recurse_subschemas_single_ref(self):

        for i in range(50):
            content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            content['$ref'] = 'http://' + self.faker.domain_name()
            schema = ISchema()
            out = yield schema._recurse_subschemas(content, None)
            self.assertEqual(schema.cached, {})
            self.assertEqual(out, {
                'schema': content,
                'success': True
            })

    @test_chainable
    def test_recurse_subschemas_faulty_ref(self):

        for i in range(50):
            content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
            content['$ref'] = self.faker.domain_name()
            schema = ISchema()
            yield self.assertFailure(schema._recurse_subschemas(content, None), RegisterException)

    @test_chainable
    def test_recurse_subschemas_list_ref(self):

        for i in range(50):
            contents = []
            for i in range(1 + self.faker.random_number(1)):
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                content['$ref'] = 'http://' + self.faker.domain_name()
                contents.append(content)

            schema = ISchema()
            out = yield schema._recurse_subschemas(contents, None)
            self.assertEqual(schema.cached, {})
            self.assertEqual(out, {
                'schema': contents,
                'success': True
            })

    @test_chainable
    def test_recurse_subschemas_endpoint(self):

        for i in range(5):

            with Patcher() as patcher:
                base_path = self.faker.file_path()

                base_contents = []
                for i in range(1 + self.faker.random_number(1)):
                    versions = {self.faker.random_number(3) for i in range(self.faker.random_number(1))}
                    versions.add(self.faker.random_number(3))
                    for v in versions:
                        content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                        schema_path = self.faker.word()

                        file = os.path.join(base_path, 'endpoints', schema_path) + '.v{}.json'.format(v)
                        if not os.path.isfile(file):
                            patcher.fs.CreateFile(file, contents=json.dumps(content))

                        base_content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                        base_content['$ref'] = 'endpoint://' + schema_path + '/v{}'.format(v)
                        base_contents.append(base_content)

                schema = ISchema()
                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                out = yield schema._recurse_subschemas(base_contents, session)
                self.assertEqual(schema.cached, {})
                self.assertEqual(out, {
                    'schema': base_contents,
                    'success': True
                })

    @test_chainable
    def test_recurse_subschemas_endpoint_fails(self):

        for i in range(5):

            with Patcher() as patcher:
                base_path = self.faker.file_path()

                base_contents = []
                for i in range(1 + self.faker.random_number(1)):
                    versions = {self.faker.random_number(3) for i in range(self.faker.random_number(1))}
                    versions.add(self.faker.random_number(3))
                    for v in versions:
                        content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                        schema_path = self.faker.word()

                        file = os.path.join(base_path, 'endpoints', schema_path) + '.v{}.json'.format(v)
                        if not os.path.isfile(file):
                            patcher.fs.CreateFile(file, contents=json.dumps(content))

                        base_content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                        base_content['$ref'] = 'endpoint://' + schema_path + 'v{}'.format(v)
                        base_contents.append(base_content)

                schema = ISchema()
                subschema = mock.MagicMock()
                subschema.flatten = mock.MagicMock(return_value=False)
                schema._schema_factory = mock.MagicMock(return_value=subschema)
                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                out = yield schema._recurse_subschemas(base_contents, session)
                self.assertEqual(schema.cached, {})
                self.assertEqual(out, {
                    'schema': base_contents,
                    'success': False
                })

    @test_chainable
    def test_recurse_subschemas_endpoint_fails2(self):

        for i in range(5):
            base_path = self.faker.file_path()
            base_content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')

            schema = ISchema()
            old = schema._recurse_subschemas
            schema._recurse_subschemas = mock.MagicMock(return_value={'schema': [], 'success': False})
            session = mock.MagicMock()
            session.component_schemas_path = mock.MagicMock(return_value=base_path)
            out = yield old(base_content, session)
            self.assertEqual(schema.cached, {})
            self.assertEqual(out, {
                'schema': base_content,
                'success': False
            })

    @test_chainable
    def test_recurse_subschemas_endpoint_no_versions(self):

        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                schema_path = self.faker.word()
                content['$ref'] = 'endpoint://' + schema_path

                patcher.fs.CreateFile(os.path.join(base_path, 'endpoints', schema_path) + '.json', contents=json.dumps(content))

                schema = ISchema()
                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                yield self.assertFailure(schema._recurse_subschemas(content, session), RegisterException)

    def test_schema_factory_resource(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            schema = self.faker.word()
            version = self.faker.random_number(1)
            resource = ISchema._schema_factory('resource', '{}/{}/{}/v{}'.format(vendor, component, schema, version))
            self.assertIsInstance(resource, ResourceSchema)
            self.assertEqual(resource.vendor, vendor)
            self.assertEqual(resource.component, component)
            self.assertEqual(resource.schema_path, schema)
            self.assertEqual(resource.versions, [version])

    def test_schema_factory_endpoint(self):

        for i in range(50):
            schema = self.faker.file_path().replace('.', '/')
            version = self.faker.random_number(1)
            endpoint = ISchema._schema_factory('endpoint', '{}/v{}'.format(schema, version))
            self.assertIsInstance(endpoint, EndpointSchema)
            self.assertEqual(endpoint.schema_path, schema)
            self.assertEqual(endpoint.versions, [version])

    def test_schema_factory_http(self):

        for i in range(50):
            schema = self.faker.domain_name()
            endpoint = ISchema._schema_factory('http', schema)
            self.assertIsInstance(endpoint, HttpsSchema)
            self.assertEqual(endpoint.uri, 'https://{}'.format(schema))

    def test_schema_factory_https(self):

        for i in range(50):
            schema = self.faker.domain_name()
            endpoint = ISchema._schema_factory('https', schema)
            self.assertIsInstance(endpoint, HttpsSchema)
            self.assertEqual(endpoint.uri, 'https://{}'.format(schema))

    def test_schema_factory_faulty(self):

        for i in range(50):
            schema = self.faker.domain_name()
            self.assertRaises(RegisterException, ISchema._schema_factory, 'random', schema)

    def test_to_schema(self):
        for i in range(50):
            with Patcher() as patcher:

                base_path = self.faker.file_path()
                schema_path = self.faker.file_path()
                versions = {self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))}
                contents = {}
                for v in versions:
                    content = self.faker.pydict(4, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                    patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v{}.json'.format(v), contents=json.dumps(content))
                    contents[v] = content

                schema = ISchema()
                schema._retrieve_local(base_path, schema_path, versions=versions)
                self.assertEqual(schema.to_schema(), {
                    'oneOf': list(contents.values())
                })

    def test_to_schema_single(self):
        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path()
                version = self.faker.random_number(3)
                content = self.faker.pydict(4, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v{}.json'.format(version), contents=json.dumps(content))

                schema = ISchema()
                schema._retrieve_local(base_path, schema_path, versions=[version])
                self.assertEqual(schema.to_schema(), content)

    def test_to_schema_failure(self):
        schema = ISchema()
        self.assertRaises(NotImplementedError, schema.to_schema)


class InlineSchemaTests(DBTestCase):
    faker = Faker()

    def test_construction(self):
        content = self.faker.pydict(4, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
        schema = InlineSchema(content)
        self.assertEqual(schema.schema, content)
        self.assertEqual(schema.cached, {})

    def test_flatten(self):
        content = self.faker.pydict(4, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
        schema = InlineSchema(content)
        schema._recurse_subschemas = mock.MagicMock(return_value={'test': 'test return'})
        out = schema.flatten({'session': 'test session'})
        self.assertEqual(out, {'test': 'test return'})
        schema._recurse_subschemas.assert_called_once_with(content, {'session': 'test session'})

    def test_to_schema(self):
        content = self.faker.pydict(4, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
        schema = InlineSchema(content)
        self.assertEqual(schema.to_schema(), content)


class HttpsSchemaTests(DBTestCase):
    faker = Faker()

    def test_construction(self):
        uri = self.faker.domain_name()
        schema = HttpsSchema(uri)
        self.assertEqual(schema.uri, 'https://' + uri)
        self.assertEqual(schema.cached, {})

    def test_flatten(self):
        uri = self.faker.domain_name()
        schema = HttpsSchema(uri)
        self.assertTrue(schema.flatten())

    def test_to_schema(self):
        uri = self.faker.domain_name()
        schema = HttpsSchema(uri)
        self.assertEqual(schema.to_schema(), {'$ref': 'https://' + uri})


class EndpointSchemaTests(DBTestCase):
    faker = Faker()

    def test_construction(self):

        for i in range(50):
            path = self.faker.word()
            version = self.faker.random_number(1)
            schema = EndpointSchema('{}/v{}'.format(path, version))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, [version])
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction2(self):

        for i in range(50):
            path = self.faker.word() + '/' + self.faker.word()
            version = self.faker.random_number(1)
            schema = EndpointSchema('{}/v{}'.format(path, version))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, [version])
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction3(self):

        for i in range(50):
            path = self.faker.file_path().replace('.', '/')
            version = self.faker.random_number(1)
            schema = EndpointSchema('{}/v{}'.format(path, version))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, [version])
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction4(self):

        for i in range(50):
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = EndpointSchema('{}/v{}'.format(path, ','.join(str(x) for x in versions)))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions)
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction5(self):

        for i in range(50):
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = EndpointSchema('{}/{}'.format(path, ','.join('v' + str(x) for x in versions)))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions)
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction6(self):

        for i in range(50):
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = EndpointSchema('{}/{}'.format(path, ','.join(str(x) for x in versions)))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions)
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction7(self):

        for i in range(50):
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            versions2 = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = EndpointSchema('{}/v{}'.format(path, ','.join(str(x) for x in versions)), versions=versions2)
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions2)
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction8(self):

        for i in range(50):
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            versions2 = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = EndpointSchema('{}/{}'.format(path, ','.join('v' + str(x) for x in versions)), versions=versions2)
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions2)
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction9(self):

        for i in range(50):
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            versions2 = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = EndpointSchema('{}/{}'.format(path, ','.join(str(x) for x in versions)), versions=versions2)
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions2)
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction10(self):

        for i in range(50):
            path = self.faker.file_path().replace('.', '/')
            schema = EndpointSchema('{}'.format(path))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, [1])
            self.assertEqual(schema.schema_subdir, 'endpoints')
            self.assertEqual(schema.cached, {})

    def test_construction_fail(self):

        for i in range(50):
            path = self.faker.domain_name()
            version = self.faker.random_number(1)
            self.assertRaises(RegisterException, EndpointSchema, '{}/v{}'.format(path, version))

    def test_construction_fail2(self):

        for i in range(50):
            path = self.faker.domain_name()
            version = self.faker.random_number(1)
            self.assertRaises(RegisterException, EndpointSchema, '{}/v-{}'.format(path, version))

    @test_chainable
    def test_flatten(self):

        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v1.json', contents=json.dumps(content))

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                schema = EndpointSchema('{}'.format(schema_path))
                self.assertTrue((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {
                    1: content
                })

    @test_chainable
    def test_flatten_cache(self):

        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v1.json', contents=json.dumps(content))

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                schema = EndpointSchema('{}'.format(schema_path))
                self.assertTrue((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {
                    1: content
                })
                session.component_schemas_path = mock.MagicMock(return_value=NotImplementedError())
                self.assertTrue((yield schema.flatten(session)))

    @test_chainable
    def test_flatten_failure(self):

        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v1.json', contents=json.dumps(content))

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                schema = EndpointSchema('{}'.format(schema_path))
                schema._recurse_subschemas = mock.MagicMock(return_value={'success': False, 'schema': content})
                self.assertFalse((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {})
                self.assertFalse((yield schema.flatten(session)))


class ClaimSchemaTests(DBTestCase):
    faker = Faker()

    def test_construction(self):
        path = self.faker.word()
        version = self.faker.random_number(1)
        schema = ClaimSchema('{}/v{}'.format(path, version))
        self.assertIsInstance(schema, EndpointSchema)
        self.assertEqual(schema.schema_path, path)
        self.assertEqual(schema.versions, [version])
        self.assertEqual(schema.schema_subdir, 'claims')
        self.assertEqual(schema.cached, {})


class ResourceSchemaTests(DBTestCase):
    faker = Faker()

    def test_construction(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.word()
            version = self.faker.random_number(1)
            schema = ResourceSchema('{}/{}/{}/v{}'.format(vendor, component, path, version))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, [version])
            self.assertEqual(schema.cached, {})

    def test_construction2(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.word() + '/' + self.faker.word()
            version = self.faker.random_number(1)
            schema = ResourceSchema('{}/{}/{}/v{}'.format(vendor, component, path, version))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, [version])
            self.assertEqual(schema.cached, {})

    def test_construction3(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.file_path().replace('.', '/')
            version = self.faker.random_number(1)
            schema = ResourceSchema('{}/{}/{}/v{}'.format(vendor, component, path, version))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, [version])
            self.assertEqual(schema.cached, {})

    def test_construction4(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = ResourceSchema('{}/{}/{}/v{}'.format(vendor, component, path, ','.join(str(x) for x in versions)))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions)
            self.assertEqual(schema.cached, {})

    def test_construction5(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = ResourceSchema('{}/{}/{}/{}'.format(vendor, component, path, ','.join('v' + str(x) for x in versions)))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions)
            self.assertEqual(schema.cached, {})

    def test_construction6(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = ResourceSchema('{}/{}/{}/{}'.format(vendor, component, path, ','.join(str(x) for x in versions)))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions)
            self.assertEqual(schema.cached, {})

    def test_construction7(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            versions2 = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = ResourceSchema('{}/{}/{}/v{}'.format(vendor, component, path, ','.join(str(x) for x in versions)), versions=versions2)
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions2)
            self.assertEqual(schema.cached, {})

    def test_construction8(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            versions2 = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = ResourceSchema('{}/{}/{}/{}'.format(vendor, component, path, ','.join('v' + str(x) for x in versions)),
                                    versions=versions2)
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions2)
            self.assertEqual(schema.cached, {})

    def test_construction9(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.file_path().replace('.', '/')
            versions = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            versions2 = list({self.faker.random_number(3) for i in range(2 + self.faker.random_number(1))})
            schema = ResourceSchema('{}/{}/{}/{}'.format(vendor, component, path, ','.join(str(x) for x in versions)), versions=versions2)
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, versions2)
            self.assertEqual(schema.cached, {})

    def test_construction10(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.file_path().replace('.', '/')
            schema = ResourceSchema('{}/{}/{}'.format(vendor, component, path))
            self.assertEqual(schema.schema_path, path)
            self.assertEqual(schema.versions, [1])
            self.assertEqual(schema.cached, {})

    def test_construction_fail(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.domain_name()
            version = self.faker.random_number(1)
            self.assertRaises(RegisterException, ResourceSchema, '{}/{}/{}/v{}'.format(vendor, component, path, version))

    def test_construction_fail2(self):

        for i in range(50):
            vendor = self.faker.word()
            component = self.faker.word()
            path = self.faker.domain_name()
            version = self.faker.random_number(1)
            self.assertRaises(RegisterException, ResourceSchema, '{}/{}/{}/v-{}'.format(vendor, component, path, version))

    @test_chainable
    def test_flatten(self):

        for i in range(50):
            with Patcher() as patcher:
                vendor = self.faker.word()
                component = self.faker.word()

                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                session.call = mock.MagicMock(return_value=content)
                schema = ResourceSchema('{}/{}/{}'.format(vendor, component, schema_path))
                self.assertTrue((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {
                    1: content
                })

                session.call.assert_called_once_with('mdstudio.schema.endpoint.get', {
                    'name': schema_path,
                    'version': 1,
                    'component': component,
                    'type': 'resource'
                }, claims={
                    'vendor': vendor
                })

    @test_chainable
    def test_flatten2(self):

        for i in range(50):
            with Patcher() as patcher:
                vendor = self.faker.word()
                component = self.faker.word()

                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v1.json', contents=json.dumps(content))

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                session.component_config = mock.MagicMock()
                session.component_config.static = mock.MagicMock()
                session.component_config.static.vendor = vendor
                session.component_config.static.component = component

                schema = ResourceSchema('{}/{}/{}'.format(vendor, component, schema_path))
                self.assertTrue((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {
                    1: content
                })

    @test_chainable
    def test_flatten3(self):

        for i in range(50):
            with Patcher() as patcher:
                vendor = self.faker.word()
                component = self.faker.word()

                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v1.json', contents=json.dumps(content))

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                session.component_config = mock.MagicMock()
                session.component_config.static = mock.MagicMock()
                session.component_config.static.vendor = vendor

                session.call = mock.MagicMock(return_value=content)
                schema = ResourceSchema('{}/{}/{}'.format(vendor, component, schema_path))
                self.assertTrue((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {
                    1: content
                })

                session.call.assert_called_once_with('mdstudio.schema.endpoint.get', {
                    'name': schema_path,
                    'version': 1,
                    'component': component,
                    'type': 'resource'
                }, claims={
                    'vendor': vendor
                })

    @test_chainable
    def test_flatten4(self):

        for i in range(50):
            with Patcher() as patcher:
                vendor = self.faker.word()
                component = self.faker.word()

                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v1.json', contents=json.dumps(content))

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                session.component_config = mock.MagicMock()
                session.component_config.static = mock.MagicMock()
                session.component_config.static.component = component

                session.call = mock.MagicMock(return_value=content)
                schema = ResourceSchema('{}/{}/{}'.format(vendor, component, schema_path))
                self.assertTrue((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {
                    1: content
                })

                session.call.assert_called_once_with('mdstudio.schema.endpoint.get', {
                    'name': schema_path,
                    'version': 1,
                    'component': component,
                    'type': 'resource'
                }, claims={
                    'vendor': vendor
                })

    @test_chainable
    def test_flatten_cache(self):

        for i in range(50):
            with Patcher() as patcher:
                vendor = self.faker.word()
                component = self.faker.word()

                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v1.json', contents=json.dumps(content))

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                session.component_config = mock.MagicMock()
                session.component_config.static = mock.MagicMock()
                session.component_config.static.vendor = vendor
                session.component_config.static.component = component
                schema = ResourceSchema('{}/{}/{}'.format(vendor, component, schema_path))
                self.assertTrue((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {
                    1: content
                })
                session.component_schemas_path = mock.MagicMock(return_value=NotImplementedError())
                self.assertTrue((yield schema.flatten(session)))

    @test_chainable
    def test_flatten_cache2(self):

        for i in range(50):
            with Patcher() as patcher:
                vendor = self.faker.word()
                component = self.faker.word()

                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v1.json', contents=json.dumps(content))

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                session.call = mock.MagicMock(return_value=content)
                schema = ResourceSchema('{}/{}/{}'.format(vendor, component, schema_path))
                self.assertTrue((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {
                    1: content
                })
                session.component_schemas_path = mock.MagicMock(return_value=NotImplementedError())
                self.assertTrue((yield schema.flatten(session)))

    @test_chainable
    def test_flatten_failure(self):

        for i in range(50):
            with Patcher() as patcher:
                vendor = self.faker.word()
                component = self.faker.word()

                base_path = self.faker.file_path()
                schema_path = self.faker.file_path().replace('.', '/')
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.v1.json', contents=json.dumps(content))

                session = mock.MagicMock()
                session.component_schemas_path = mock.MagicMock(return_value=base_path)
                schema = ResourceSchema('{}/{}/{}'.format(vendor, component, schema_path))
                schema._recurse_subschemas = mock.MagicMock(return_value={'success': False, 'schema': content})
                self.assertFalse((yield schema.flatten(session)))
                self.assertEqual(schema.cached, {})
                self.assertFalse((yield schema.flatten(session)))


class ValidateTests(TestCase):
    def test_validate_json_schema(self):
        validate_json_schema({'format': 'uri', 'type': 'string'}, 'https://example.com')

    def test_validate_json_schema_fail(self):
        self.assertRaises(ValidationError, validate_json_schema, {'format': 'uri', 'type': 'string'}, 2)

    def test_validate_json_schema_fail2(self):
        self.assertRaises(ValidationError, validate_json_schema, {'format': 'uri', 'type': 'string'}, 'example')


class MDStudioClaimSchemaTests(TestCase):
    def test_construction(self):
        with Patcher() as patcher:
            session = mock.MagicMock()
            session.mdstudio_schemas_path = mock.MagicMock(return_value='schemas')

            patcher.fs.CreateFile('schemas/claims.json', contents='{"test": "json"}')
            schema = MDStudioClaimSchema(session)
            self.assertIs(schema, MDStudioClaimSchema(session))
            self.assertEqual(schema.to_schema(), {'test': 'json'})
            MDStudioClaimSchema._instance = None

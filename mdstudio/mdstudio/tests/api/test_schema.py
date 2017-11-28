import json
from unittest import TestCase

import os
from faker import Faker
from pyfakefs.fake_filesystem_unittest import Patcher

from mdstudio.api.schema import ISchema


class ISchemaTests(TestCase):

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
                    0: content
                })

    def test_retrieve_local_not_exists(self):
        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path()

                schema = ISchema()
                self.assertRaises(FileNotFoundError, schema._retrieve_local, base_path, schema_path)

    def test_retrieve_local_versoin(self):
        for i in range(50):
            with Patcher() as patcher:
                base_path = self.faker.file_path()
                schema_path = self.faker.file_path()
                content = self.faker.pydict(10, True, 'str', 'str', 'str', 'str', 'float', 'int', 'int', 'uri', 'email')
                patcher.fs.CreateFile(os.path.join(base_path, schema_path) + '.json', contents=json.dumps(content))

                schema = ISchema()
                schema._retrieve_local(base_path, schema_path)
                self.assertEqual(schema.cached, {
                    0: content
                })

from copy import deepcopy
from jsonschema import ValidationError
from pyfakefs.fake_filesystem_unittest import Patcher
from unittest import TestCase

import os
from autobahn.wamp import ComponentConfig
from faker import Faker
from mock import mock, call

from mdstudio.component.impl.common import CommonSession


class TestCommonSession(TestCase):

    faker = Faker()

    def setUp(self):

        class TestSession(CommonSession):
            load_settings = mock.MagicMock()
            validate_settings = mock.MagicMock()
            extract_custom_scopes = mock.MagicMock(return_value={'scopes': True})
        self.session = TestSession()

    def test_construction(self):
        self.assertIsInstance(self.session.component_config, CommonSession.Config)

        self.assertIsInstance(self.session.component_config.session, CommonSession.Config.Session)
        self.assertIsInstance(self.session.component_config.session, dict)

        self.assertIsInstance(self.session.component_config.static, CommonSession.Config.Static)
        self.assertIsInstance(self.session.component_config.static, dict)

        self.assertIsInstance(self.session.component_config.session, dict)

        self.session.validate_settings.assert_called_once_with()
        self.session.load_settings.assert_called_once_with()
        self.session.extract_custom_scopes.assert_called_once_with()
        self.assertEqual(self.session.function_scopes, {'scopes': True})

    def test_construction2(self):
        class TestSession(CommonSession):
            load_environment = mock.MagicMock()
            validate_settings = mock.MagicMock()
        self.session = TestSession()
        self.session.load_environment.assert_called_once_with(self.session.session_env_mapping)


    def test_construction_config(self):

        class TestSession(CommonSession):
            validate_settings = mock.MagicMock()
        config = ComponentConfig()
        self.assertEqual(config.realm, None)
        self.session = TestSession(config)
        self.assertEqual(config.realm, 'mdstudio')

    @mock.patch.dict(os.environ, {'MDSTUDIO_USERNAME': 'TEST_VALUE'})
    def test_construction_username(self):

        class TestSession(CommonSession):
            validate_settings = mock.MagicMock()
        self.session = TestSession()
        self.assertEqual(self.session.component_config.session.username, 'TEST_VALUE')

    @mock.patch.dict(os.environ, {'MDSTUDIO_PASSWORD': 'TEST_VALUE'})
    def test_construction_password(self):

        class TestSession(CommonSession):
            validate_settings = mock.MagicMock()
        self.session = TestSession()
        self.assertEqual(self.session.component_config.session.password, 'TEST_VALUE')

    @mock.patch.dict(os.environ, {'MDSTUDIO_REALM': 'TEST_VALUE'})
    def test_construction_realm(self):

        class TestSession(CommonSession):
            validate_settings = mock.MagicMock()
        self.session = TestSession()
        self.assertEqual(self.session.component_config.session.realm, 'TEST_VALUE')

    def test_construction_order(self):

        class TestSession(CommonSession):
            def load_settings(self):
                assert (self.environment)
            def load_environment(self, mapping):
                self.environment = True
            def validate_settings(self):
                assert (self.pre_init)
            def extract_custom_scopes(self):
                assert (self.component_config)
                self.extracted = True
            def pre_init(self):
                assert (self.extracted)
                self.pre_init = True
            def on_init(self):
                assert (self.pre_init)
                self.on_init = True

        session = TestSession()
        self.assertTrue(session.pre_init)
        self.assertTrue(session.on_init)

    def test_add_session_env_var(self):
        var = self.faker.word()
        env = self.faker.word()
        self.assertEqual(self.session.component_config.session, {'realm': 'mdstudio'})
        self.session.add_session_env_var(var, [env], extract=lambda x: x)

        self.assertEqual(self.session.component_config.session, {
            'realm': 'mdstudio',
            var: env
        })

    @mock.patch.dict(os.environ, {'TEST2': 'VALUE'})
    def test_add_session_env_var_multiple(self):
        var = 'TEST'
        env = self.faker.word()
        env2 = 'TEST2'
        self.assertEqual(self.session.component_config.session, {'realm': 'mdstudio'})
        self.session.add_session_env_var(var, [env, env2])

        self.assertEqual(self.session.component_config.session, {
            'realm': 'mdstudio',
            var: 'VALUE'
        })

    @mock.patch.dict(os.environ, {'TEST2': 'VALUE2', 'TEST3': 'VALUE3'})
    def test_add_session_env_var_multiple2(self):
        var = 'TEST'
        env = 'TEST2'
        env2 = 'TEST3'
        self.assertEqual(self.session.component_config.session, {'realm': 'mdstudio'})
        self.session.add_session_env_var(var, [env, env2])

        self.assertEqual(self.session.component_config.session, {
            'realm': 'mdstudio',
            var: 'VALUE2'
        })

    @mock.patch.dict(os.environ, {'TEST2': 'VALUE'})
    def test_add_session_env_var_single(self):
        var = 'TEST'
        env = 'TEST2'
        self.assertEqual(self.session.component_config.session, {'realm': 'mdstudio'})
        self.session.add_session_env_var(var, env)

        self.assertEqual(self.session.component_config.session, {
            'realm': 'mdstudio',
            var: 'VALUE'
        })

    def test_add_session_env_var_default(self):
        var = self.faker.word()
        env = self.faker.word()
        default = self.faker.word()
        self.assertEqual(self.session.component_config.session, {'realm': 'mdstudio'})
        self.session.add_session_env_var(var, env, default)

        self.assertEqual(self.session.component_config.session, {
            'realm': 'mdstudio',
            var: default
        })

    def test_add_session_env_var_none(self):
        var = self.faker.word()
        env = self.faker.word()
        self.assertEqual(self.session.component_config.session, {'realm': 'mdstudio'})
        self.session.add_session_env_var(var, env)

        self.assertEqual(self.session.component_config.session, {
            'realm': 'mdstudio'
        })

    def test_load_environment(self):
        class TestSession(CommonSession):
            validate_settings = mock.MagicMock()
            add_session_env_var = mock.MagicMock()

        self.session = TestSession()
        self.session.add_session_env_var.assert_has_calls([
            call('username', ['MDSTUDIO_USERNAME'], None),
            call('password', ['MDSTUDIO_PASSWORD'], None),
            call('realm', ['MDSTUDIO_REALM'], 'mdstudio')
        ])

    def test_load_settings(self):

        class TestSession(CommonSession):
            validate_settings = mock.MagicMock()

        with Patcher() as patcher:
            file = os.path.join(self.session.component_root_path, 'settings.yml')
            patcher.fs.CreateFile(file, contents='{"test": 2}')
            self.session = TestSession()

            self.assertEqual(self.session.component_config.settings['test'], 2)

    def test_load_settings_yaml_over_json(self):

        class TestSession(CommonSession):
            validate_settings = mock.MagicMock()

        with Patcher() as patcher:
            file = os.path.join(self.session.component_root_path, 'settings.json')
            file2 = os.path.join(self.session.component_root_path, 'settings.yml')
            patcher.fs.CreateFile(file, contents='{"test": 2}')
            patcher.fs.CreateFile(file2, contents='{"test": 3}')
            self.session = TestSession()

            self.assertEqual(self.session.component_config.settings['test'], 3)

    def test_load_settings_dot_json_over_yaml(self):

        class TestSession(CommonSession):
            validate_settings = mock.MagicMock()

        with Patcher() as patcher:
            file = os.path.join(self.session.component_root_path, 'settings.yml')
            file2 = os.path.join(self.session.component_root_path, '.settings.json')
            patcher.fs.CreateFile(file, contents='{"test": 2}')
            patcher.fs.CreateFile(file2, contents='{"test": 3}')
            self.session = TestSession()

            self.assertEqual(self.session.component_config.settings['test'], 3)

    def test_load_settings_dot_yaml_over_dot_json(self):

        class TestSession(CommonSession):
            validate_settings = mock.MagicMock()

        with Patcher() as patcher:
            file = os.path.join(self.session.component_root_path, '.settings.json')
            file2 = os.path.join(self.session.component_root_path, '.settings.yml')
            patcher.fs.CreateFile(file, contents='{"test": 2}')
            patcher.fs.CreateFile(file2, contents='{"test": 3}')
            self.session = TestSession()

            self.assertEqual(self.session.component_config.settings['test'], 3)

    def test_session_env_mapping(self):

        self.assertEqual(self.session.session_env_mapping, {
            'password': (['MDSTUDIO_PASSWORD'], None),
            'realm': (['MDSTUDIO_REALM'], 'mdstudio'),
            'username': (['MDSTUDIO_USERNAME'], None)
        })

    def test_session_update_var(self):

        self.assertEqual(self.session.session_update_vars, {
            'username': 'authid',
            'role': 'authrole',
            'session_id': 'session'
        })

    def test_class_name(self):

        self.assertEqual(self.session.class_name, "TestSession")

    def test_component_root_path(self):

        self.assertEqual(self.session.component_root_path, os.path.realpath(os.path.join(os.path.dirname(__file__), '../')))

    def test_component_schemas_path(self):

        self.assertEqual(self.session.component_schemas_path, os.path.realpath(os.path.join(os.path.dirname(__file__), 'schemas')))

    def test_mdstudio_root_path(self):

        self.assertEqual(self.session.mdstudio_root_path, os.path.realpath(os.path.join(os.path.dirname(__file__), '../../../../')))

    def test_mdstudio_schemas_path(self):

        self.assertEqual(self.session.mdstudio_schemas_path, os.path.realpath(os.path.join(os.path.dirname(__file__), '../../../schemas')))

    def test_settings_files(self):

        self.assertEqual(self.session.settings_files, [
            'settings.json',
            'settings.yml',
            '.settings.json',
            '.settings.yml'
        ])

    def test_settings_schemas(self):

        self.assertEqual(self.session.settings_schemas, [
            os.path.join(self.session.component_schemas_path, 'settings.json'),
            os.path.join(self.session.mdstudio_schemas_path, 'settings.json')
        ])

    def test_validate_settings(self):
        class TestSession(CommonSession):
            pass

        with Patcher() as patcher:
            file = os.path.join(self.session.component_schemas_path, 'settings.json')
            patcher.fs.CreateFile(file, contents='{"type": "object", "properties": {"test": {"type": "string"}}, "required": ["test"]}')
            self.assertRaisesRegex(ValidationError, '\'test\' is a required property', TestSession)

    def test_validate_settings2(self):
        class TestSession(CommonSession):
            pass

        with Patcher() as patcher:
            file = os.path.join(self.session.component_schemas_path, 'settings.json')
            file2 = os.path.join(self.session.mdstudio_schemas_path, 'settings.json')
            patcher.fs.CreateFile(file, contents='{"type": "object", "properties": {"session": {"type": "object"}}, "required": ["session"]}')
            patcher.fs.CreateFile(file2, contents='{"type": "object", "properties": {"test": {"type": "string"}}, "required": ["test"]}')

            self.assertRaisesRegex(ValidationError, '\'test\' is a required property', TestSession)

    def test_validate_settings3(self):
        class TestSession(CommonSession):
            pass

        with Patcher() as patcher:
            file = os.path.join(self.session.component_schemas_path, 'settings.json')
            file2 = os.path.join(self.session.mdstudio_schemas_path, 'settings.json')
            patcher.fs.CreateFile(file2, contents='{"type": "object", "properties": {"session": {"type": "object"}}, "required": ["session"]}')
            patcher.fs.CreateFile(file, contents='{"type": "object", "properties": {"test": {"type": "string"}}, "required": ["test"]}')

            self.assertRaisesRegex(ValidationError, '\'test\' is a required property', TestSession)

    def test_validate_settings4(self):
        class TestSession(CommonSession):
            pass

        with Patcher() as patcher:
            TestSession()
from copy import deepcopy
from unittest import TestCase

import os
from autobahn.wamp import ComponentConfig
from faker import Faker
from mock import mock

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








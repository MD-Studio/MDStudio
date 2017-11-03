import os
from autobahn.wamp import PublishOptions
from mock import mock

from lie_db import DBWampApi
from lie_db.db_methods import MongoDatabaseWrapper
from mdstudio.deferred.chainable import chainable
from mdstudio.unittest.api import APITestCase
from mdstudio.unittest.db import DBTestCase
from mdstudio.util import WampSchema


class TestWampService(DBTestCase, APITestCase):

    def setUp(self):
        self.service = DBWampApi()
        self.service._extract_namespace = mock.MagicMock(return_value='test.namespace')
        self.db = mock.MagicMock(spec=MongoDatabaseWrapper)
        self.service._client.get_namespace = mock.MagicMock(return_value=self.db)

    def test_preInit(self):

        self.service.preInit()

        self.assertEqual(self.service.session_config_template, {})
        self.assertEqual(self.service.package_config_template, WampSchema('db', 'settings/settings'))
        self.assertEqual(self.service.session_config['loggernamespace'], 'db')

    def test_onInit(self):

        self.service.onInit()

        self.assertEqual(self.service._client._host, "localhost")
        self.assertEqual(self.service._client._port, 27017)
        self.assertEqual(self.service.autolog, False)
        self.assertEqual(self.service.autoschema, False)

    @mock.patch.dict(os.environ, {'MD_MONGO_HOST': 'localhost2'})
    def test_onInit_host(self):

        self.service.onInit()

        self.assertEqual(self.service._client._host, "localhost2")

    @mock.patch.dict(os.environ, {'MD_MONGO_PORT': '31312'})
    def test_onInit_port(self):

        self.service.onInit()

        self.assertEqual(self.service._client._port, 31312)

    @mock.patch.dict(os.environ, {'MD_MONGO_PORT': '31312'})
    def test_onRun(self):

        self.service.publish = mock.MagicMock()
        self.service.onRun(None)

        self.service.publish.assert_called_once_with(u'mdstudio.db.endpoint.events.online', True, options=self.service.publish_options)

    def test_more(self):

        self.assertApi(self.service ,'more', {
            'cursorId' : 123456
        }, {})

        self.db.more.assert_called_once_with(123456)
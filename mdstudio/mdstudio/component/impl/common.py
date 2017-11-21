import inspect
import json
from collections import OrderedDict

import re
from copy import deepcopy

import os

import yaml
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp import PublishOptions, ApplicationError
from autobahn.wamp.request import Publication
from twisted.internet import reactor

from mdstudio.api.api_result import APIResult
from mdstudio.api.call_exception import CallException
from mdstudio.api.converter import convert_obj_to_json
from mdstudio.api.schema import validate_json_schema
from mdstudio.collection import merge_dicts
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from twisted.python.failure import Failure

from mdstudio.deferred.sleep import sleep
from mdstudio.logging.impl.session_observer import SessionLogObserver
from mdstudio.logging.log_type import LogType
from mdstudio.logging.logger import Logger
from mdstudio.utc import now


class CommonSession(ApplicationSession):
    class Config(object):
        class Static(dict):
            @property
            def vendor(self):
                return self.get('vendor')

            @property
            def component(self):
                return self.get('component')

        class Session(dict):
            @property
            def username(self):
                return self.get('username')

            @property
            def password(self):
                return self.get('password')

            @property
            def realm(self):
                return self.get('realm')

            @property
            def role(self):
                return self.get('role')

            @property
            def session_id(self):
                return self.get('session_id')

        def __init__(self):
            self.static = self.Static()
            self.session = self.Session()
            self.settings = {}

        def to_dict(self):
            return {
                'static': self.static,
                'session': self.session,
                'settings': self.settings
            }

    def __init__(self, config=None):
        self.log = Logger(namespace=self.__class__.__name__)
        self.log_type = LogType.User

        self.component_config = self.Config()
        self.function_scopes = self.extract_custom_scopes()
        self.load_environment(self.session_env_mapping)

        self.load_settings()

        self.pre_init()

        self.log_collector = SessionLogObserver(self, self.log_type)

        super(CommonSession, self).__init__(config)

        # load config from env/file, check with schema
        self.validate_settings()

        if config:
            config.realm = u'{}'.format(self.component_config.session.realm)

        self.on_init()

    def pre_init(self):
        pass

    def on_init(self):
        pass

    def on_run(self):
        pass

    def on_exit(self):
        pass

    def authorize_request(self, uri, claims):
        self.log.warn("Authorization for {uri} should be implemented in the component", uri=uri)

        return False

    # noinspection PyMethodOverriding
    @chainable
    def call(self, procedure, request, claims=None, **kwargs):
        if claims is None:
            claims = {}

        signed_claims = yield super(CommonSession, self).call(u'mdstudio.auth.endpoint.sign', claims)

        request = deepcopy(request)
        convert_obj_to_json(request)

        @chainable
        def make_original_call():
            res = yield super(CommonSession, self).call(procedure, request, signed_claims=signed_claims, **kwargs)

            if not isinstance(res, dict):
                res = APIResult(result=res)

            return_value(res)

        try:
            result = yield make_original_call()
        except ApplicationError as e:
            result = APIResult(error='Call to {uri} failed'.format(uri=procedure))

        if 'expired' in result:
            signed_claims = yield super(CommonSession, self).call(u'mdstudio.auth.endpoint.sign', claims)

            try:
                result = yield make_original_call()
            except ApplicationError as e:
                result = APIResult(error='Call to {uri} failed'.format(uri=procedure))

        if 'expired' in result:
            raise CallException(result['expired'])

        if 'error' in result:
            raise CallException(result['error'])

        if 'warning' in result:
            self.log.warn(result['warning'])

        if 'result' not in result:
            result['result'] = None

        return_value(result['result'])

    @chainable
    def publish(self, topic, *args, claims=None, **kwargs):
        if claims is None:
            claims = {}

        signed_claims = yield super(CommonSession, self).call(u'mdstudio.auth.endpoint.sign', claims)

        options = kwargs.pop('options', None) or PublishOptions(acknowledge=True, exclude_me=False)

        result = yield super(CommonSession, self).publish(topic, *args, signed_claims=signed_claims, options=options,
                                                          **kwargs)  # type: Publication

        return_value(result)

    def subscribe(self, handler, topic, options=None):
        @chainable
        def _handler(*args, signed_claims=None, **kwargs):
            claims = yield super(CommonSession, self).call('mdstudio.auth.endpoint.verify', signed_claims)

            if not ('error' in claims or 'expired' in claims):
                claims = claims['claims']

                if not self.authorize_request(topic, claims):
                    self.log.warn("Unauthorized publish to {topic}", topic=topic)
                else:
                    return_value((yield handler(*args, claims=claims, **kwargs)))

        return super(CommonSession, self).subscribe(_handler, topic, options)

    def event(self, topic, *args, **kwargs):
        return super(CommonSession, self).publish(topic, *args, **kwargs)

    def on_event(self, handler, topic, options=None):
        return super(CommonSession, self).subscribe(handler, topic, options)

    @chainable
    def _on_join(self):
        yield self.upload_schemas()

        yield self.on_run()

        yield self.log_collector.start_flushing(self)

    @chainable
    def on_join(self):
        registrations = yield self.register(self)

        failures = 0
        for r in registrations:
            if isinstance(r, Failure):
                self.log.info("ERROR: {class_name}: {message}", class_name=self.class_name(), message=r.value)
                failures = failures + 1

        if failures > 0:
            self.log.info("ERROR {class_name}: failed to register {procedures} procedures", procedures=failures,
                          class_name=self.class_name())

        self.log.info("{class_name}: {procedures} procedures successfully registered",
                      procedures=len(registrations) - failures, class_name=self.class_name())

        reactor.callLater(1, self._on_join)

    @chainable
    def onJoin(self, details):
        yield self.flatten_endpoint_schemas()

        # Update session config, they may have been changed by the application authentication method
        for var, details_var in self.session_update_vars.items():
            self.component_config.session[var] = getattr(details, details_var)

        reactor.callLater(1, self.on_join)

    # @chainable
    # def on_leave(self, details):
    #     self.log.info('{class_name} is leaving realm {realm}', class_name=self.class_name(),
    #                   realm=self.component_config.session.realm)
    #
    #     yield self.on_exit()
    #
    #     yield super(CommonSession, self).onLeave(details)
    #     yield self.disconnect()
    #
    # onLeave = on_leave

    def add_session_env_var(self, session_var, env_vars, default=None, extract=os.getenv):
        if not isinstance(env_vars, list):
            env_vars = [env_vars]

        for var in env_vars:
            env_var = extract(var)

            if env_var:
                self.component_config.session[session_var] = env_var
                return

        if default:
            self.component_config.session[session_var] = default

    def load_environment(self, mapping):
        for session_var, env_vars in mapping.items():
            self.add_session_env_var(session_var, env_vars[0], env_vars[1])

    def load_settings(self):
        for file in self.settings_files():
            settings_file = os.path.join(self.component_root_path(), file)

            if os.path.isfile(settings_file):
                with open(settings_file, 'r') as f:
                    merge_dicts(self.component_config.settings, yaml.load(f))

    def validate_settings(self):
        for path in self.settings_schemas():
            if os.path.isfile(path):
                with open(path, 'r') as f:
                    settings_schema = json.load(f)

                validate_json_schema(settings_schema, self.component_config.to_dict())

    def extract_custom_scopes(self):
        function_scopes = []

        # Scan for scopes on registrations
        for key, f in self.__class__.__dict__.items():
            try:
                function_scopes.append({
                    'scope': f.scope,
                    'uri': f.uri
                })
            except AttributeError:
                pass

        return function_scopes

    @chainable
    def upload_schemas(self):
        schemas = {
            'endpoints': self._collect_schemas('endpoints'),
            'resources': self._collect_schemas('resources')
        }

        yield self.call(u'mdstudio.schema.endpoint.upload', {
            'component': self.component_config.static.component,
            'schemas': schemas
        }, claims={'vendor': self.component_config.static.vendor})

        self.log.info('Uploaded schemas for {package}', package=self.class_name())

    def _collect_schemas(self, *sub_paths):
        schemas = []
        root_dir = os.path.join(self.component_schemas_path(), *sub_paths)

        if os.path.isdir(root_dir):
            for root, dirs, files in os.walk(root_dir):
                if files:
                    for file in files:
                        path = os.path.join(root, file)
                        rel_path = os.path.relpath(path, root_dir).replace('\\', '/')
                        path_decomposition = re.match('(.*?)\\.?(v\\d+)?\\.json', rel_path)

                        with open(path, 'r') as f:
                            schema_entry = {
                                'schema': json.load(f),
                                'name': path_decomposition.group(1)
                            }

                        if path_decomposition.group(2):
                            schema_entry['version'] = int(path_decomposition.group(2).strip('v'))

                        schemas.append(schema_entry)

        return schemas

    @chainable
    def flatten_endpoint_schemas(self):
        # Scan for input/output schemas on registrations
        for key, f in self.__class__.__dict__.items():
            func = getattr(self, key)
            try:
                yield func.input_schema.flatten(self)
            except AttributeError:
                pass
            try:
                yield func.output_schema.flatten(self)
            except AttributeError:
                pass
            try:
                yield func.claims_schema.flatten(self)
            except AttributeError:
                pass

    @property
    def session_env_mapping(self):
        return OrderedDict([
            ('username', (['MDSTUDIO_USERNAME'], None)),
            ('password', (['MDSTUDIO_PASSWORD'], None)),
            ('realm', (['MDSTUDIO_REALM'], 'mdstudio'))
        ])

    @property
    def session_update_vars(self):
        return OrderedDict([
            ('username', 'authid'),
            ('role', 'authrole'),
            ('session_id', 'session')
        ])

    @classmethod
    def class_name(cls):
        return cls.__name__

    @classmethod
    def component_root_path(cls):
        return os.path.dirname(os.path.dirname(inspect.getfile(cls)))

    @classmethod
    def component_schemas_path(cls):
        return os.path.join(os.path.dirname(inspect.getfile(cls)), 'schemas')

    @classmethod
    def mdstudio_root_path(cls):
        return os.path.normpath(os.path.join(os.path.dirname(inspect.getfile(CommonSession)), '..', '..', '..'))

    @classmethod
    def mdstudio_schemas_path(cls):
        return os.path.abspath(os.path.join(os.path.dirname(inspect.getfile(CommonSession)), '..', '..', 'schemas'))

    @classmethod
    def settings_files(cls):
        return ['settings.json', 'settings.yml', '.settings.json', '.settings.yml']

    @classmethod
    def settings_schemas(cls):
        return [os.path.join(cls.component_schemas_path(), 'settings.json'),
                os.path.join(cls.mdstudio_schemas_path(), 'settings.json')]

import inspect
import json
from copy import deepcopy

import os

import yaml
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp import PublishOptions
from autobahn.wamp.request import Publication

from mdstudio.api.call_exception import CallException
from mdstudio.api.converter import convert_obj_to_json
from mdstudio.api.schema import validate_json_schema
from mdstudio.collection import merge_dicts
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from twisted.python.failure import Failure

from mdstudio.logging.logger import Logger


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

        self.component_config = self.Config()
        self.function_scopes = self.extract_custom_scopes()
        self.load_environment(self.session_env_mapping)

        self.load_settings()

        self.pre_init()

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
        result = yield super(CommonSession, self).call(procedure, request, signed_claims=signed_claims, **kwargs)

        if 'expired' in result:
            signed_claims = yield super(CommonSession, self).call(u'mdstudio.auth.endpoint.sign', claims)

            result = yield super(CommonSession, self).call(u'{}'.format(procedure), request, signed_claims=signed_claims,
                                                           **kwargs)

        if 'expired' in result:
            raise CallException(result['expired'])

        if 'error' in result:
            raise CallException(result['error'])

        if 'warning' in result:
            self.log.warn(result['warning'])

        convert_obj_to_json(result)

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
    def on_join(self, details):
        registrations = yield self.register(self)

        failures = 0
        for r in registrations:
            if isinstance(r, Failure):
                self.log.info("ERROR: {class_name}: {message}", class_name=self.class_name, message=r.value)
                failures = failures + 1

        if failures > 0:
            self.log.info("ERROR {class_name}: failed to register {procedures} procedures", procedures=failures,
                          class_name=self.class_name)

        self.log.info("{class_name}: {procedures} procedures successfully registered",
                      procedures=len(registrations) - failures, class_name=self.class_name)

        # Update session config, they may have been changed by the application authentication method
        for var, details_var in self.session_update_vars.items():
            self.component_config.session[var] = getattr(details, details_var)

        yield self.on_run()

    onJoin = on_join

    @chainable
    def on_leave(self, details):
        self.log.info('{class_name} is leaving realm {realm}', class_name=self.class_name,
                      realm=self.component_config.session.realm)

        yield self.on_exit()

        yield super(CommonSession, self).onLeave(details)

    onLeave = on_leave

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
        for file in self.settings_files:
            settings_file = os.path.join(self.component_root_path, file)

            if os.path.isfile(settings_file):
                with open(settings_file, 'r') as f:
                    merge_dicts(self.component_config.settings, yaml.load(f))

    def validate_settings(self):
        for path in self.settings_schemas:
            if os.path.isfile(path):
                with open(path, 'r') as f:
                    settings_schema = json.load(f)

                validate_json_schema(settings_schema, self.component_config.to_dict())

    def extract_custom_scopes(self):
        function_scopes = []

        # Scan for input/output schemas on registrations
        for key, f in self.__class__.__dict__.items():
            try:
                function_scopes.append({
                    'scope': f.scope,
                    'uri': f.uri
                })
            except AttributeError:
                pass

        return function_scopes

    @property
    def session_env_mapping(self):
        return {
            'username': (['MDSTUDIO_USERNAME'], None),
            'password': (['MDSTUDIO_PASSWORD'], None),
            'realm': (['MDSTUDIO_REALM'], 'mdstudio')
        }

    @property
    def session_update_vars(self):
        return {
            'username': 'authid',
            'role': 'authrole',
            'session_id': 'session'
        }

    @property
    def class_name(self):
        return type(self).__name__

    @property
    def component_root_path(self):
        return os.path.dirname(os.path.dirname(inspect.getfile(self.__class__)))

    @property
    def component_schemas_path(self):
        return os.path.join(os.path.dirname(inspect.getfile(self.__class__)), 'schemas')

    @property
    def mdstudio_root_path(self):
        return os.path.normpath(os.path.join(os.path.dirname(inspect.getfile(CommonSession)), '..', '..', '..'))

    @property
    def mdstudio_schemas_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(inspect.getfile(CommonSession)), '..', '..', 'schemas'))

    @property
    def settings_files(self):
        return ['settings.json', 'settings.yml', '.settings.json', '.settings.yml']

    @property
    def settings_schemas(self):
        return [os.path.join(self.component_schemas_path, 'settings.json'),
                os.path.join(self.mdstudio_schemas_path, 'settings.json')]

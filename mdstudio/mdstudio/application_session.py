# -*- coding: utf-8 -*-

import inspect
import itertools
import json
import os
import re

import twisted
from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp import auth, cryptosign
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.logger import Logger
from twisted.python.failure import Failure
from twisted.python.logfile import DailyLogFile

from mdstudio.api.call_exception import CallException
from mdstudio.api.schema import Schema, validate_json_schema
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.logging import WampLogObserver, PrintingObserver
from mdstudio.util import resolve_config


class BaseApplicationSession(ApplicationSession):
    """
    BaseApplicationSession class

    Inherits from the Autobahn Twisted based `ApplicationSession 
    <http://autobahn.ws/python/reference/autobahn.twisted.html#autobahn.twisted.wamp.ApplicationSession>`_
    and extends it with methods to ease the process of automatic authentication,
    authorization and WAMP API configuration.

    It does so by overriding the five `placeholder methods <http://autobahn.ws/python/wamp/programming.html>`_
    that the ApplicationSession calls over the course of the session life cycle:

    * **onConnect**: first stage in establishing connection with the WAMP router
      (Crossbar). Define the rules of engagement; realm to join, authentication
      method to use.
    * **onChallenge**: authenticate using any of the Crossbar supported `methods <http://crossbar.io/docs/Authentication/>`_.
    * **onJoin**: register the API methods with the WAMP router and update local
      API configuration with settings retrieved by calling ``mdstudio.config.get``
    * **onLeave**: cleanup methods when leaving the realm
    * **onDisconnect**: cleanup methods when disconnecting from the WAMP router

    To enable custom events during the application life cycle, the
    BaseApplicationSession defines it's own placeholder methods. Do not override
    the five methods mentioned above but use these instead:

    * **onInit**: called at the end of the class constructor.
    * **onRun**: implement custom code to be called automatically when the WAMP
      session joins the realm. Called from the onJoin method.
    * **onExit**: cleanup methods called from the onLeave method.

    Logging: the Autobahn ApplicationSession initiates an instance of the
    Twisted logger as self.log
    """

    require_config = []

    def __init__(self, config=None, **kwargs):
        """
        Class constructor

        Extending the Autobahn ApplicationSession constructor with variable
        initiation routines for WAMP session authentication, authorization
        and API configuration. These variables are stored in two objects:

        * session_config: stores all variables related to the current session
          in a WAMPTaskMetaData object
        * package_config: stores all variables needed to run the package
          specific methods the API exposes.

        The variables that populate these two objects may be defined in
        three different ways depending on the context in which the
        BaseApplicationSession is being used:

        * Application session configuration using the config object. This is
          the default way of configuration used when starting a session
          with the autobahn ApplicationRunner or when starting components
          using the Crossbar router with configuration defined in the
          config.json file. The `extra` argument defined in the config
          object is reserved for custom data to be passed to the
          ApplicationSession constructor.

          If the `extra` argument is a dictionary you may define a
          package_config variable as dictionary of file path to a JSON file
          containing the package configuration in there that will be used to
          update the class package_config. All other key/value pairs will be
          used to update the session_config dictionary. If the `extra` argument
          is not a dictionary it will remain available in the config object
          accessible as self.config.

        * Arguments provided directly to the class constructor. Usefull when
          starting an application session using a a WAMP component factory.
          Default keyword argument is `package_config` to update the class
          package_config dictionary in a similar way as defined above.
          Any other keyword arguments are used to update the session_config
          dictionary.

        * Arguments defined using system environment variables parsed using
          os.environ are used to update session_config. Available variables:
          - MD_AUTH_REALM = Crossbar WAMP realm to join
          - MD_AUTH_METHOD = WAMP authentication method to use
          - MD_AUTH_USERNAME = username for authentication
          - MD_AUTH_PASSWORD = password for authentication

        The constructor checks all of these configuration options in sequence.

        Optional keyword arguments:
        :param package_config: package or module specific configuration
        :type package_config:  dict or file path
        :param package_name:   name of the package exposing WAMP API methods.
                               is used for identification and retrieval of
                               configuration from the configuration server.
                               Defaults to the first element of the canonical
                               __module__ variable.
        :type package_name:    str
        :param authid:         username or ID for authentication
        :type authid:          str
        :param password:       password for authentication
        :type password:        str
        """

        # initialize defaults
        self.session_config_environment_variables = {
            'authid': 'MD_AUTH_USERNAME',
            'password': 'MD_AUTH_PASSWORD',
            'realm': 'MD_AUTH_REALM',
            'authmethod': 'MD_AUTH_METHOD',
            'loggernamespace': 'MD_LOGGER_NAMESPACE'
        }

        self.function_scopes = []

        # Scan for input/output schemas on registrations
        for key, f in self.__class__.__dict__.items():
            try:
                self.function_scopes.append({
                    'scope': f.scope,
                    'uri': f.uri
                })
            except AttributeError:
                pass

        # determine namespace
        namespace = re.match('lie_(.+)', self.__module__.split('.')[0])
        self.component_info = {
            'namespace': namespace.group(1) if namespace else 'unknown',
            'package_name': self.__module__.split('.')[0],
            'class_name': type(self).__name__,
            'module_path': os.path.dirname(inspect.getfile(self.__class__)),
            'mdstudio_lib_path': os.path.dirname(__file__)
        }

        self.package_config_template = Schema('mdstudio://settings/settings')
        self.package_config_template.flatten(self)
        self.package_config_template = self.package_config_template.to_schema()
        self.session_config_template = Schema('mdstudio://session_config/session_config')
        self.session_config_template.flatten(self)
        self.session_config_template = self.session_config_template.to_schema()

        self.component_config = {
            'session': {},
            'settings': {}
        }

        # self.session_config = ConfigHandler()
        self.session_config = {}
        if namespace:
            self.session_config['loggernamespace'] = 'namespace-{}'.format(namespace.group(1))

        # determine package config directory
        package_config_dir = os.path.join(os.path.dirname(self.component_info.get('module_path')), 'data')
        if not os.path.isdir(package_config_dir):
            os.makedirs(package_config_dir)
        self._config_dir = package_config_dir

        package_logs_dir = os.path.join(package_config_dir, 'logs')
        if not os.path.isdir(package_logs_dir):
            os.makedirs(package_logs_dir)

        # call pre init to override above values
        self.preInit(**kwargs)

        # replace default logger to support proper namespace
        self.log = Logger(namespace=self.component_info.get('namespace'))

        # Init toplevel ApplicationSession
        super(BaseApplicationSession, self).__init__(config)

        extra = config.extra if config and isinstance(config.extra, dict) else {}

        # Set package_config: first global package config, the package_config
        # argument and finaly config.extra
        # self.package_config = ConfigHandler()
        self.package_config = {}
        self.package_config.update(resolve_config(extra.get('package_config')))
        self.session_config.update(resolve_config(extra.get('sesion_config')))

        # Update session_info with key/value pairs in config.extra except
        # for package config
        for key, value in extra.items():
            if key not in ('session_config', 'package_config'):
                self.session_config[key] = value

        # Load client private key (raw format) if any
        self._key = None
        if u'key' in self.session_config:
            self._load_public_key(self.session_config.get(u'key'))

        package_config_file = os.path.join(package_config_dir, 'settings.json')

        package_conf = resolve_config(package_config_file)

        if validate_json_schema(self, self.package_config_template, package_conf):
            self.package_config.update(package_conf)

            if not os.path.isfile(package_config_file):
                with open(package_config_file, 'w') as f:
                    json.dump(package_conf, f, indent=4, sort_keys=True)

        session_config_file = os.path.join(package_config_dir, 'session_config.json')
        session_conf = resolve_config(session_config_file)

        dotenvfile = os.getenv('MD_DOTENV', os.path.join(package_config_dir, '.env'))

        if os.path.isfile(dotenvfile):
            env = config_from_dotenv(dotenvfile)
        else:
            env = {}

        for key, value in self.session_config_environment_variables.items():
            if value in env:
                session_conf[key] = u'{}'.format(env[value])
            elif key in env:
                session_conf[key] = u'{}'.format(env[key])
            elif value in os.environ:
                session_conf[key] = u'{}'.format(os.environ[value])

        if validate_json_schema(self, self.session_config_template, session_conf):
            self.session_config.update(session_conf)

        # start wamp logger for buffering
        f = None
        templogs = os.path.join(self._config_dir, 'wamplogs.temp')
        if os.path.isfile(templogs):
            f = open(templogs)
        self.wamp_logger = WampLogObserver(self, f, self.session_config.get('log_level', 'info'))
        if f:
            f.close()
            os.remove(templogs)
        twisted.python.log.addObserver(self.wamp_logger)

        # start file logger
        log_file = DailyLogFile('daily.log', package_logs_dir)
        self.file_logger = PrintingObserver(log_file, self.component_info.get('namespace'),
                                            self.session_config.get('log_level', 'info'))
        twisted.python.log.addObserver(self.file_logger)

        # Configure config object
        if config:
            config.realm = u'{}'.format(self.session_config.get('realm', config.realm))

        if 'authmethod' in self.session_config.keys() and not isinstance(self.session_config.get('authmethod'), list):
            self.session_config['authmethod'] = [self.session_config.get('authmethod')]

        self.autolog = True
        self.autoschema = True

        # Call onInit hook
        self.onInit(**kwargs)

    def _load_public_key(self, key):
        """
        Load a clients public key signed using Ed25519 from a file into a
        cryptosign object to use for siging of the challenge upon
        establishing a WAMP session.

        :param key: filename of the client SSH Ed25519 public key.
        """

        try:
            self._key = cryptosign.SigningKey.from_raw_key(key)
        except Exception as e:
            self.log.error("could not load client private key: {log_failure}", log_failure=e)
            self.leave()
        else:
            self.log.debug("client public key loaded: {}".format(self._key.public_key()))

    @inlineCallbacks
    def onConnect(self):
        """
        Autobahn onConnect handler

        Establishing the transport layer to the Crossbar router.
        Defines the `realm` to connect on, the authentication method,
        authid (username) and any extra's to send along.
        """

        extra = {}

        # Define authentication method
        authmethod = self.session_config.get('authmethod')
        if authmethod and u'cryptosign' in authmethod:

            # create a proxy signing key with the private key being held in SSH agent
            # if the key has not yet been loaded in raw format.
            if not self._key:
                self._key = yield cryptosign.SSHAgentSigningKey.new(self.session_config.get(u'pubkey'))

            # authentication extra information for wamp-cryptosign
            extra[u'pubkey'] = self._key.public_key()
            extra[u'channel_binding'] = u'tls-unique'

        # Establish transport layer
        self.join(self.config.realm,
                  authmethods=authmethod,
                  authid=self.session_config.get('authid', None),
                  authrole=None,
                  authextra=extra)

    def onChallenge(self, challenge):
        """
        Autobahn onChallenge handler

        Implements WAMP authentication and authorization for connection
        of clients to the Crossbar WAMP broker using all of the Crossbar
        supported methods (http://crossbar.io/docs/Authentication/).
        The method to use is defined in the Crossbar configuration file
        (/data/crossbar/config.json), please consult the Crossbar
        documentation for the required configuration settings for these
        methods.

        Depending on the `realm` the WAMP session tries to connect to the
        following authentication methods are supported:

        * WAMP-Anonymous: anonymous authentication needs to be explicitly
          defined and is by default not allowed. If defined, `onChallenge`
          will not be called.
        * WAMP-Ticket:  a simple cleartext challenge scheme.
        * WAMP-CRA: WAMP-Challenge-Response-Authentication using a secret
          shared between the client and server side. The secret never
          travels the wire and WAMP-CRA supports salted passwords.
        * WAMP-cryptosign: a WAMP-level authentication mechanism which
          uses Curve25519-based cryptography - Ed25519 private signing keys.
        * WAMP-cookie: for client having access to a cookie store (mostly
          browser based clients) this method will place a transient or
          persistent cookie allowing for immediate authentication when a
          client connects again. You have to activate cookie-tracking and at
          least one non-cookie based authentication method for the initial
          authentication.
        * WAMP-TLS: uses the TLS client certificate for authentication.
          Providing a WAMP authid (password) is optional. This is transport
          level authentication rather then session level and is therefor
          handeled by the onConnect method.

        :param challenge: challenge object containing the challenge type
                          and any of the arguments required by the challenge
                          method to perform the authentication.
        :type challenge:  obj
        """

        self.log.debug("Recieved WAMP authentication challenge type '{method}'", method=challenge.method)

        # WAMP-Ticket based authentication
        if challenge.method == u"ticket":
            return self.session_config.get('password', None)

        # WAMP-CRA based authentication
        elif challenge.method == u"wampcra":

            # Salted password
            if u'salt' in challenge.extra:
                key = auth.derive_key(self.session_config.get('password', None),
                                      challenge.extra['salt'],
                                      challenge.extra['iterations'],
                                      challenge.extra['keylen'])
            else:
                key = self.session_config.get('password', None)

            signature = auth.compute_wcs(key, challenge.extra['challenge'])
            return signature

        # WAMP-Cryptosign based authentication. Signing the challenge is done
        # within the SSH agent which means that the private key is only touched
        # by the SSH agent itself.
        elif challenge.method == u'cryptosign' and self._key:
            return self._key.sign_challenge(self, challenge)

        # Unknow challenge type, exit.
        else:
            raise Exception("don't know how to handle authmethod {}".format(challenge.method))

    @inlineCallbacks
    def onJoin(self, details):
        """
        Autobahn onJoin handler

        When the WAMP session is initiated and the client joins the realm, this
        function is called to register methods and retrieve configuration from
        the config module.
        When done, the method calls the onRun hook responsible for custom tasks
        that need to be run automatically at client startup.

        .. caution::
           onJoin overrides the Autobahn ApplicationSession onJoin method with
           a few vital methods for the LIEStudio application. Do not overload it
           but put custom code in the onRun method instead!

        :param details: Session details
        :type details:  Autobahn SessionDetails object
        """

        # Register methods
        res = yield self.register(self)

        failures = 0
        for r in res:
            if isinstance(r, Failure):
                self.log.info("ERROR: {class_name}: {message}", class_name=self.component_info.get('class_name'),
                              message=r.value)
                failures = failures + 1

        if failures > 0:
            self.log.info("ERROR {class_name}: failed to register {procedures} procedures", procedures=failures,
                          class_name=self.component_info.get('class_name'))

        self.log.info("{class_name}: {procedures} procedures successfully registered", procedures=len(res) - failures,
                      class_name=self.component_info.get('class_name'))

        # Update session_config, they may have been changed by the application authentication method
        for session_param in ('authid', 'session', 'authrole', 'authmethod'):
            self.session_config[session_param] = getattr(details, session_param)

        # Retrieve package configuration based on package_name and update package_config
        # Try to establish a MongoDB database connection if lie_db configuration available
        def handle_retrieve_config_error(failure):
            self.log.warn('Unable to retrieve configuration for {0}'.format(self.component_info.get('package_name')))

        # self.require_config.append(self.session_config.get('package_name'))
        # self.require_config.append('lie_logger.global_log_level')
        # server_config = self.call(u'mdstudio.config.get', self.require_config)
        # server_config.addCallback(self.package_config.update)
        # # server_config.addCallback(self._establish_database_connection)
        # server_config.addErrback(handle_retrieve_config_error)

        # Add self.disconnect to Event trigger in order to get propper shutdown
        # and exit of reactor event loop on Ctrl-C e.d.
        # reactor.addSystemEventTrigger('before', 'shutdown', self.leave)

        if self.autolog:
            self.wamp_logger.start_flushing()
        else:
            def logger_event(event):
                self.wamp_logger.start_flushing()
                self.logger_subscription.unsubscribe()
                self.logger_subscription = None

            self.log.info('Delayed logging for {package}', package=self.component_info['package_name'])
            self.logger_subscription = yield self.subscribe(logger_event, u'mdstudio.logger.endpoint.events.online')

        if self.autoschema:
            self._upload_schemas()
        else:
            def schema_event(event):
                self._upload_schemas()
                self.schema_subscription.unsubscribe()
                self.schema_subscription = None

            self.log.info('Delayed schema registration for {package}', package=self.component_info['package_name'])
            self.schema_subscription = yield self.subscribe(schema_event, u'mdstudio.schema.endpoint.events.online')

        self._register_scopes()

        reactor.addSystemEventTrigger('before', 'shutdown', self.onCleanup)

        # Call onRun hook.
        yield self.onRun(details)

    def onCleanup(self, *args, **kwargs):
        self.wamp_logger.stop_flushing()
        f = open(os.path.join(self._config_dir, 'wamplogs.temp'), 'w')
        self.wamp_logger.flush_remaining(f)
        f.close()

    @inlineCallbacks
    def onLeave(self, details):
        """
        Autobahn onLeave handler

        Called when the ApplicationSession is about to leave the Crossbar
        WAMP realm.
        When done, the method calls the onExit hook responsible for custom
        tasks that need to be run automatically at realm leave.

        :param details: Session details
        :type details:  Autobahn SessionDetails object
        """

        self.log.info('{class_name} of {package_name} is leaving realm {realm}', realm=self.session_config.get('realm'),
                      **self.component_info)

        # Call onExit hook
        yield self.onExit(details)

        super(BaseApplicationSession, self).onLeave(details)

    @inlineCallbacks
    def onDisconnect(self):
        self.log.info('{class_name} of {package_name} disconnected from realm {realm}',
                      realm=self.session_config.get('realm'),
                      **self.component_info)

        self.wamp_logger.stop_flushing()

        res = yield super(BaseApplicationSession, self).onDisconnect()

        returnValue(res)

    # Class placeholder methods. Override these for custom events during 
    # application life cycle
    def preInit(self, **kwargs):
        """
        Implement custom code to be called before the application class is
        initiated. Override config templates here.
        """

        return

    def onInit(self, **kwargs):
        """
        Implement custom code to be called when the application class is
        initiated.
        """

        return

    def onRun(self, details):
        """
        Implement custom code to be called when the WAMP session joins the
        realm. Called from the onJoin method.

        .. note::
           do not forget to use the @inlineCallbacks decorator on the method
           in case it returns a generator

        :param details: Session details
        :type details:  Autobahn SessionDetails object
        """

        return

    def onExit(self, details):
        """
        Implement custom code to be called when the application leaves the
        WAMP realm.

        :param details: Session details
        :type details:  Autobahn SessionDetails object
        """

        return

    def get_schema(self, schema_path, module_path=None):
        if module_path is None:
            module_path = self.component_info.get('module_path')

        if not schema_path.endswith('.json'):
            schema_path = '{}.json'.format(schema_path)
        else:
            self.log.debug('WARNING: json schema {} does not have to end with .json'.format(schema_path))

        schema_abs_path = os.path.join(module_path, 'schema', schema_path)

        if os.path.isfile(schema_abs_path):
            with open(schema_abs_path) as json_file:
                return json.load(json_file)

        self.log.error('ERROR: Schema not found in {}'.format(schema_abs_path))

        return None

    @inlineCallbacks
    def flush_logs(self, namespace, log_list):
        res = yield self.publish(u'mdstudio.logger.endpoint.log.{}'.format(namespace), {'logs': log_list},
                                 options=wamp.PublishOptions(acknowledge=True, exclude_me=False))

        returnValue({})

    @chainable
    def _upload_schemas(self):
        schemas = {
            'endpoint': self._collect_schemas('schema', 'endpoint'),
            'resource': self._collect_schemas('schema', 'resource')
        }

        yield self.call(u'mdstudio.schema.endpoint.upload', {
            'component': self.component_info['namespace'],
            'schemas': schemas
        }, auth_meta={'vendor': 'mdstudio'})

        self.log.info('Registered schemas for {package}', package=self.component_info['package_name'])

    def _collect_schemas(self, *sub_paths):
        schemas = []
        root_dir = os.path.join(self.component_info['module_path'], *sub_paths)

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

    @inlineCallbacks
    def _register_scopes(self):
        if self.function_scopes:
            res = yield self.call(
                'mdstudio.auth.endpoint.oauth.registerscopes.{}'.format(self.component_info.get('namespace')),
                {'scopes': self.function_scopes})

            self.log.info('Registered {count} scopes for {package}', count=len(self.function_scopes),
                          package=self.component_info['package_name'])

    @chainable
    def call(self, procedure, *args, auth_meta=None, **kwargs):
        if auth_meta is None:
            auth_meta = {}

        signed_meta = yield super(BaseApplicationSession, self).call(u'mdstudio.auth.endpoint.sign', auth_meta)

        result = yield super(BaseApplicationSession, self).call(procedure, *args, signed_meta=signed_meta, **kwargs)

        if 'expired' in result:
            signed_meta = yield super(BaseApplicationSession, self).call(u'mdstudio.auth.endpoint.sign', auth_meta)

            result = yield super(BaseApplicationSession, self).call(u'{}'.format(procedure), *args, signed_meta=signed_meta, **kwargs)

        if 'expired' in result:
            raise CallException(result['expired'])

        if 'error' in result:
            raise CallException(result['error'])

        if 'warning' in result:
            self.log.warn(result['warning'])

        # @todo: refresh jwt if invalid
        return_value(result['result'])

    def authorize_request(self, uri, auth_meta):
        self.log.warn("This should be implemented in the component")

        return False

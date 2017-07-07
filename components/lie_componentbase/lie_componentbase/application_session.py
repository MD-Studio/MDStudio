# -*- coding: utf-8 -*-

import jsonschema
import inspect
import json
import time
import sys
import os
import re

from autobahn.wamp import auth, cryptosign
from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor
from autobahn import wamp
from twisted.python.failure import Failure
from pprint import pprint

from .wamp_taskmeta import WAMPMessageEnvelope
from .wamp_logging import WampLogging
from .util import PY2, PY3, resolve_config, DefaultValidatingDraft4Validator, block_on

from .config.config_handler import ConfigHandler

if PY3:
    from .util import unicode      

def wamp_schema_handler(session):
    def handler(uri):
        @inlineCallbacks
        def resolve(uri):
            module_name = session.__module__.split('.')[0]
            schema_path_match = re.match('wamp://liestudio\.([a-z]+)\.schemas/(.+)', uri)
            if not schema_path_match:
                session.log.error("Not a proper wamp uri")
                
            # schema_path_groups = schema_path_groups.groups()
            schema_path = schema_path_match.group(2)
            
            if 'lie_{}'.format(schema_path_match.group(1)) == module_name:
                res = yield session.get_schema(schema_path)
            elif 'lie_{}'.format(schema_path_match.group(1)) == 'lie_componentbase':
                res = yield session.get_schema(schema_path, os.path.dirname(inspect.getfile(CoreApplicationSession)))
            else:
                res = yield session.call(u'liestudio.{}.schemas', schema_path)

            if res is None:
                self.log.warn('WARNING: could not retrieve a valid schema')
                res = {}
            
            returnValue(res)

        return block_on(resolve(uri))

    return handler

def validate_json_schema(session, schema_def, request):
    schema = {'$ref': schema_def} if type(schema_def) in (str, unicode) else schema_def
    
    resolver = jsonschema.RefResolver.from_schema(schema, handlers={'wamp': wamp_schema_handler(session)})
    validator=DefaultValidatingDraft4Validator(schema, resolver=resolver)
    
    valid = True
    try:
        validator.validate(request)
    except jsonschema.ValidationError as e:
        session.log.error(e.message)
        valid = False

    return valid
    
def wamp_register(uri, input_schema, output_schema, options=None):
    def wrap_f(f):
        @wamp.register(uri, options)
        @inlineCallbacks
        def wrapped_f(self, request, **kwargs):
            self.log.info('DEBUG: validating input with schema {}'.format(input_schema))
            if not validate_json_schema(self, input_schema, request):
                res = yield {}
                returnValue(res)

            res = yield f(self, request, **kwargs)
        
            self.log.debug('DEBUG: validating output with schema {}'.format(output_schema))
            validate_json_schema(self, output_schema, res)
            
            returnValue(res)

        return wrapped_f
    
    return wrap_f

class BaseApplicationSession(ApplicationSession):
    """
    BaseApplicationSession class

    Inherits from the Autobahn Twisted based `ApplicationSession <http://autobahn.ws/python/reference/autobahn.twisted.html#autobahn.twisted.wamp.ApplicationSession>`_
    and extends it with methods to ease the process of automatic authentication,
    authorization and WAMP API configuration.

    It does so by overriding the five `placeholder methods <http://autobahn.ws/python/wamp/programming.html>`_
    that the ApplicationSession calls over the course of the session life cycle:

    * **onConnect**: first stage in establishing connection with the WAMP router
      (Crossbar). Define the rules of engagement; realm to join, authentication
      method to use.
    * **onChallenge**: authenticate using any of the Crossbar supported `methods <http://crossbar.io/docs/Authentication/>`_.
    * **onJoin**: register the API methods with the WAMP router and update local
      API configuration with settings retrieved by calling ``liestudio.config.get``
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

    def __init__(self, config, package_config=None, **kwargs):
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
          - _LIE_WAMP_REALM = Crossbar WAMP realm to join
          - _LIE_AUTH_METHOD = WAMP authentication method to use
          - _LIE_AUTH_USERNAME = username for authentication
          - _LIE_AUTH_PASSWORD = password for authentication

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

        # we cannot use default argument {} since it stores references internally,
        # making subsequent constructions unpredictable
        if package_config is None:
            package_config = {}

        # Init session_config with default values
        self.session_info = WAMPMessageEnvelope(realm=config.realm,
                                                package_name=self.__module__.split('.')[0],
                                                class_name=type(self).__name__
        )

        # Update session_config with key/value pairs in config.extra except
        # for package config
        extra = config.extra if isinstance(config.extra, dict) else {}

        self.session_config = ConfigHandler()
        self.session_config.update(resolve_config(extra.get('sesion_config')))
        self.session_config.update(kwargs)

        for key, value in extra.items():
            if not key.endswith('_config'):
                self.session_info.set(key,value)

        # Init toplevel ApplicationSession
        super(BaseApplicationSession, self).__init__(config)

        # Load client private key (raw format) if any
        self._key = None
        if u'key' in self.session_config:
            self._load_public_key(self.session_config[u'key'])

        # Set package_config: first global package config, the package_config
        # argument and finaly config.extra
        self.package_config = ConfigHandler()
        self.package_config.update(resolve_config(package_config))
        self.package_config.update(resolve_config(extra.get('package_config')))


        if '_LIE_CONFIG_DIR' in os.environ:
            config_dir = os.environ['_LIE_CONFIG_DIR']
        elif 'config_dir' in extra.keys():
            config_dir = extra['config_dir']
        else:
            # Assume config is stored relative to the working directory when the application is started
            config_dir = './data'

        package_config_dir = os.path.join(config_dir, self.session_info['package_name'])
        if not os.path.isdir(package_config_dir):
            os.makedirs(package_config_dir)

        package_config_file = os.path.join(package_config_dir, 'settings.json')
        # Set default template
        package_config_template = 'wamp://liestudio.componentbase.schemas/settings/v1'
        # Override with custom template given in the constructor
        if hasattr(self, 'package_config_template'):
            package_config_template = self.package_config_template
        # Override with custom template given in the extra variable
        package_config_template = extra.get('package_config_template', package_config_template)

        if not os.path.isfile(package_config_file):
            package_conf = {}
            if validate_json_schema(self, package_config_template, package_conf):
                with open(package_config_file, 'w') as f:
                    json.dump(package_conf, f, indent=4, sort_keys=True)
        else:
            package_conf = resolve_config(package_config_file)

        if validate_json_schema(self, extra.get('package_config_template', package_config_template), package_conf):
            self.package_config.update(package_conf)

        session_config_file = os.path.join(package_config_dir, 'session_config.json')
        # Set default template
        session_config_template = 'wamp://liestudio.componentbase.schemas/session_config/v1'
        # Override with custom template given in the constructor
        if hasattr(self, 'session_config_template'):
            session_config_template = self.session_config_template
        # Override with custom template given in the extra variable
        session_config_template = extra.get('session_config_template', self.package_config.get('session_config_template', session_config_template))

        if not os.path.isfile(session_config_file):
            session_conf = {}
            if validate_json_schema(self, session_config_template, session_conf):
                with open(session_config_file, 'w') as f:
                    json.dump(session_conf, f, indent=4, sort_keys=True)
        else:
            session_conf = resolve_config(session_config_file)

        if validate_json_schema(self, session_config_template, session_conf):
            self.session_config.update(session_conf)        


        # Configure config object
        config.realm = self.session_config.get('realm', config.realm)

        if 'authmethod' in self.session_config.keys() and not isinstance(self.session_config['authmethod'], list):
            self.session_config['authmethod'] = [self.session_config['authmethod']]

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
        authmethod = self.session_config.authmethod
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

        self.log.debug("Recieved WAMP authentication challenge type '{0}'".format(challenge.method))

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
        schemas = yield self.register(self.get_schema, u'liestudio.{}.schemas'.format(re.match('lie_([a-z]+)', self.session_info['package_name']).group(1)))
        res.append(schemas)

        failures = 0
        for r in res:
            if isinstance(r, Failure):
                self.log.info("ERROR: {class_name}: {message}".format(class_name=self.session_info.class_name, message=r.value.message))
                failures = failures + 1

        if failures > 0:
            self.log.info("ERROR {class_name}: failed to register {procedures} procedures", procedures=failures, class_name=self.session_info.class_name)

        self.log.info("{class_name}: {procedures} procedures successfully registered", procedures=len(res)-failures, class_name=self.session_info.class_name)

        # Update session_info, they may have been changed by the application
        # authentication method
        for session_param in ('authid', 'session', 'authrole', 'authmethod'):
            self.session_info[session_param] = getattr(details,session_param)

        # Retrieve package configuration based on package_name and update package_config
        # Try to establish a MongoDB database connection if lie_db configuration available
        def handle_retrieve_config_error(failure):
            self.log.warn('Unable to retrieve configuration for {0}'.format(self.session_info.get('package_name')))

        # self.require_config.append(self.session_config.get('package_name'))
        # self.require_config.append('lie_logger.global_log_level')
        # server_config = self.call(u'liestudio.config.get', self.require_config)
        # server_config.addCallback(self.package_config.update)
        # # server_config.addCallback(self._establish_database_connection)
        # server_config.addErrback(handle_retrieve_config_error)

        # Init WAMP logging
        self.logger = WampLogging(wamp=self, log_level=self.package_config.get('global_log_level', 'info'))

        # Add self.disconnect to Event trigger in order to get propper shutdown
        # and exit of reactor event loop on Ctrl-C e.d.
        reactor.addSystemEventTrigger('before', 'shutdown', self.disconnect)

        # Call onRun hook.
        self.onRun(details)

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

        self.log.info('{class_name} of {package_name} is leaving realm {realm}', **self.session_info.dict())

        # Call onExit hook
        self.onExit(details)

    def task(self, method, *args, **kwargs):
        """
        Wrapper around ApplicationSession `call` method.

        Ensure that the right method is being called, method arguments
        and keyword argumnents are being provided and the current session
        data is passed along.
        """

        self.logger.debug('Call method {0}'.format(method))
        
        if 'session' in kwargs:
            session_config = WAMPTaskMetaData(metadata=kwargs.get('session'))
            del kwargs['session']
        else:    
            session_config = self.session_config
        
        return self.call(method, session=session_config(), *args, **kwargs)
    
    # Class placeholder methods. Override these for custom events during 
    # application life cycle
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

    def get_schema(self, schema_path, module_path = None):
        if module_path is None:
            module_path = os.path.dirname(inspect.getfile(self.__class__))

        if not schema_path.endswith('.json'):
            schema_path = '{}.json'.format(schema_path)
        else:
            self.log.debug('WARNING: json schema {} does not have to end with .json'.format(schema_path))

        schema_abs_path = os.path.join(module_path, 'schema', schema_path)

        if os.path.isfile(schema_abs_path): 
            return json.load(open(schema_abs_path))

        return None

# -*- coding: utf-8 -*-

import json
import os
import time

from   autobahn.wamp          import auth, cryptosign
from   autobahn.twisted.wamp  import ApplicationSession
from   twisted.internet.defer import inlineCallbacks
from   twisted.logger         import Logger

try:
    from   lie_config import get_config, ConfigHandler
    LIECONFIG = True
except:
    LIECONFIG = False

# LieApplicationSession variables names defined in os.envrion
ENVIRON = {'_LIE_WAMP_REALM':'realm',
           '_LIE_AUTH_METHOD':'auth_method',
           '_LIE_AUTH_USERNAME':'username',
           '_LIE_AUTH_PASSWORD':'password'}

def _load_settings_from_config_extra(config):
    
    if config.extra:
        
        # Check if extra is file path and try load as JSON
        if type(config.extra) == str and os.path.isfile(config.extra):
            settings = {}
            with open(config.extra) as cf:
                try:
                    settings = json.loads(cf.read()).decode('utf-8')
                except:
                    pass
            return settings
        
        # Check if extra is a dict, return
        if type(config.extra) == dict:
            return config.extra
    
    return {}

class LieApplicationSession(ApplicationSession):

    logging = Logger()
    
    def __init__(self, config=None, **kwargs):
        """
        Class constructor

        Extending the ApplicationSession constructor with variable initiation
        routines to enable WAMP session authentication and authorization.
        These variables may be defined in three different ways depending on
        the context in which the LieApplicationSession is being used:

        * Application session configuration using the config object. This is
          the default way of configuration used when starting a session
          with the autobahn ApplicationRunner or when starting components
          using the Crossbar router with configuration defined in the
          config.json file. Custom settings can be define using the
          config.extra attribute.
        * Arguments provided directly to the class constructor. Usefull when
          starting an application session using a a WAMP component factory.
        * Arguments defined using system environment variables parsed using
          os.environ:
          - _LIE_WAMP_REALM = Crossbar WAMP realm to join
          - _LIE_AUTH_METHOD = WAMP authentication method to use
          - _LIE_AUTH_USERNAME = username for authentication
          - _LIE_AUTH_PASSWORD = password for authentication

        The constructor checks all of these configuration options in sequence.

        Optional keyword arguments:
        :param package_config: package or module specific configuration
        :type package_config:  dict
        :param package_name:   name of the package exposing WAMP API methods.
                               is used for identification and retrieval of
                               configuration from the configuration server.
                               Defaults to the first element of the canonical
                               __module__ variable.
        :type package_name:    str
        :param username:       username for authentication
        :type username:        str
        :param password:       password for authentication
        :type password:        str
        """
        
        #Set session_config: first ApplicationSessio config, then kwargs then os.environ
        self.session_config = config.extra if type(config.extra) == dict else {}
        self.session_config.update(kwargs)
        self.session_config.update(dict([(ENVIRON[k],os.environ[k]) for k in ENVIRON if k in os.environ]))
        
        # Component vars
        self._package_name = self.session_config.get('package_name', self.__module__.split('.')[0])

        # Configure config object
        config.realm = self.session_config.get('realm', config.realm)

        # Init toplevel ApplicationSession
        ApplicationSession.__init__(self, config)
        
        # Load client private key (raw format) if any
        self._key = None
        if u'key' in self.session_config:
            self._load_public_key(self.session_config[u'key'])
        
        # Init package specific configuration
        if LIECONFIG:
            self.package_config = get_config(self._package_name)
            self.package_config.update(self.session_config.get('package_config',{}))
        else:
            self.package_config = self.session_config.get('package_config',{})

        # Update package configuration with configuration extra's if defined.
        self.package_config.update(_load_settings_from_config_extra(config))
    
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
            self.logging.error("could not load client private key: {log_failure}", log_failure=e)
            self.leave()
        else:
            self.logging.debug("client public key loaded: {}".format(self._key.public_key()))
    
    @property
    def auth_method(self):
        """
        Returns the Crossbar WAMP authentication method to use
        A WAMP connection can possibly allow for multiple authentication
        methods.
        
        :rtype: list or None
        """
        
        auth_method = self.session_config.get('auth_method', None)
        if not auth_method:
            return None

        if hasattr(auth_method, '__iter__'):
            return [auth_method]

        return [auth_method]

    @property
    def username(self):
        """
        Return username, utf-8 unicode encoded.
        """
        
        return self.session_config.get('username', None)
        
    @property
    def password(self):
        """
        Return password, utf-8 unicode encoded.
        """
        
        return self.session_config.get('password', None)
    
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
        auth_method = self.auth_method
        if auth_method and u'cryptosign' in auth_method:

            # create a proxy signing key with the private key being held in SSH agent
            # if the key has not yet been loaded in raw format.
            if not self._key:
                self._key = yield cryptosign.SSHAgentSigningKey.new(self.session_config.get(u'pubkey'))

            # authentication extra information for wamp-cryptosign
            extra[u'pubkey'] = self._key.public_key()
            extra[u'channel_binding'] = u'tls-unique'
        
        # Establish transport layer
        self.join(self.config.realm,
                  authmethods=self.auth_method,
                  authid=self.username,
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

        self.logging.debug("Recieved WAMP authentication challenge type '{0}'".format(challenge.method))

        # WAMP-Ticket based authentication
        if challenge.method == u"ticket":
            return self.password

        # WAMP-CRA based authentication
        elif challenge.method == u"wampcra":

            # Salted password
            if u'salt' in challenge.extra:
                key = auth.derive_key(self.password,
                                      challenge.extra['salt'],
                                      challenge.extra['iterations'],
                                      challenge.extra['keylen'])

            else:
                key = self.password

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
        Report the methods that this application interface registers with
        the Crossbar router.
        """

        # Fetch the module configuration from the server
        res = yield self.register(self)
        self.logging.debug("{0}: {1} procedures registered".format(type(self).__name__, len(res)))
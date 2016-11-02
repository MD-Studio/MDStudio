# -*- coding: utf-8 -*-

import json
import os
import time

from   autobahn.wamp          import auth, cryptosign
from   autobahn.twisted.wamp  import ApplicationSession
from   twisted.internet.defer import inlineCallbacks

from   lie_config             import get_config, ConfigHandler

# LieApplicationSession variables names defined in os.envrion
ENVIRON = {'_LIE_WAMP_REALM':'realm',
           '_LIE_AUTH_METHOD':'auth_method',
           '_LIE_AUTH_USERNAME':'username',
           '_LIE_AUTH_PASSWORD':'password'}

def _resolve_package_config(package_config):
    """
    Resolve the package_config as dictionary
    
    Check if input type is a dictionary, return.
    Check if the input type is a valid file path to a JSON configuration file,
    load as dictionary.
    
    This function always returns a dictionary, empty or not.
    
    :param package_config: package configuration to resolve
    :type package_config:  mixed
    :return:               package_configuration
    :rtype:                dict
    """
    
    settings = {}
    if package_config:
        
        if type(package_config) in (dict, ConfigHandler):
            return package_config
        
        if type(package_config) in (str, unicode):
            package_config = os.path.abspath(package_config)
            if os.path.isfile(package_config):
            
                with open(package_config) as cf:
                    try:
                        settings = json.load(cf)
                    except:
                        pass
    
    return settings
            

class LieApplicationSession(ApplicationSession):
    """
    LieApplicationSession class
    
    Inherits from the Autobahn Twisted based `ApplicationSession <http://autobahn.ws/python/reference/autobahn.twisted.html#autobahn.twisted.wamp.ApplicationSession>`_
    and extends it with methods to ease the process of automatic authentication,
    authorization and WAMP API configuration.
    
    It does so by overriding the five `placeholder methods <http://autobahn.ws/python/wamp/programming.html>`_ 
    that the ApplicationSession calls over the course of the session life cycle:
    
    * onConnect: first stage in establishing connection with the WAMP router
      (Crossbar). Define the rules of engagement; realm to join, authentication
      method to use.
    * onChallenge: authenticate using any of the Crossbar supported `methods <http://crossbar.io/docs/Authentication/>`_.
    * onJoin: register the API methods with the WAMP router and update local
      API configuration with settings retrieved by calling liestudio.config.get
    * onLeave: cleanup methods when leaving the realm
    * onDisconnect: cleanup methods when disconnecting from the WAMP router
    
    To enable custom events during the application life cycle, the 
    LieApplicationSession defines it's own placeholder methods. Do not override
    the five methods mentioned above but use these instead:
    
    * onInit: called at the end of the class constructor.
    * onRun: implement custom code to be called automatically when the WAMP 
      session joins the realm. Called from the onJoin method.
    * onExit: cleanup methods called from the onLeave method.
    
    Logging: the Autobahn ApplicationSession initiates an instance of the 
    Twisted logger as self.log
    """
    
    def __init__(self, config, package_config={}, **kwargs):
        """
        Class constructor

        Extending the Autobahn ApplicationSession constructor with variable 
        initiation routines for WAMP session authentication, authorization
        and API configuration. These variables are stored in two dictionaries:
        
        * session_config: stores all variables related to the current session
        * package_config: stores all variables needed to run the package
          specific methods the API exposes.
        
        The variables that populate these two dictionaries may be defined in
        three different ways depending on the context in which the 
        LieApplicationSession is being used:

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
        
        # Init session_config with default values
        self.session_config = {
            'realm': config.realm,
            'package_name': self.__module__.split('.')[0],
            'class_name': type(self).__name__
        }
        
        # Update session_config with key/value pairs in config.extra except
        # for package config
        extra = config.extra if type(config.extra) == dict else {}
        for key, value in extra.items():
            if key != 'package_config':
                self.session_config[key] = value
        
        # Update session_config with kwargs and environmental variables
        self.session_config.update(kwargs)
        self.session_config.update(dict([(ENVIRON[k],os.environ[k]) for k in ENVIRON if k in os.environ]))
        
        # Configure config object
        config.realm = self.session_config.get('realm', config.realm)

        # Init toplevel ApplicationSession
        ApplicationSession.__init__(self, config)
        
        # Load client private key (raw format) if any
        self._key = None
        if u'key' in self.session_config:
            self._load_public_key(self.session_config[u'key'])
        
        # Set package_config: first global package config, the package_config
        # argument and finaly config.extra
        self.package_config = get_config()
        self.package_config.update(_resolve_package_config(package_config))
        self.package_config.update(_resolve_package_config(extra.get('package_config')))
        
        # Call onInit hook
        self.onInit()
    
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
    
    @property
    def auth_method(self):
        """
        Returns the Crossbar WAMP authentication method to use.
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
        self.log.info("{class_name}: {procedures} procedures registered", procedures=len(res), **self.session_config)
        
        # Update session_config, they may have been changed by the application
        # authentication method
        for session_param in ('authid','session','authrole','authmethod'):
            self.session_config[session_param] = getattr(details,session_param)
        
        # Retrieve package configuration based on package_name and update package_config
        def handle_retrieve_config_error(failure):
            self.log.warn('Unable to retrieve configuration for {0}'.format(self.session_config.get('package_name')))
        
        server_config = self.call(u'liestudio.config.get', self.session_config.get('package_name'))
        server_config.addCallback(self.package_config.update)
        server_config.addErrback(handle_retrieve_config_error)
        
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

        self.log.debug('{class_name} of {package_name} is leaving realm {realm}', **self.session_config)

        # Call onExit hook
        self.onExit(details)
    
    # Class placeholder methods. Override these for custom events during 
    # application life cycle
    def onInit(self):
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
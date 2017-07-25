# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import re
import copy
import json
import base64
import itertools

from autobahn import wamp
from autobahn.wamp.exception import ApplicationError
from twisted.logger import Logger
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock
from oauthlib import oauth2
from oauthlib.common import Request as OAuthRequest, generate_client_id as generate_secret
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from lie_componentbase import BaseApplicationSession, WampSchema, register
from lie_componentbase import db
from .util import check_password, hash_password, ip_domain_based_access, generate_password
from .password_retrieval import PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE
from .oauth.request_validator import OAuthRequestValidator

class AuthWampApi(BaseApplicationSession):
    """
    User management WAMP methods.
    """

    log = Logger()

    def preInit(self, **kwargs):
        self.session_config_template = WampSchema('auth', 'session_config/session_config', 1)
        self.package_config_template = WampSchema('auth', 'settings/settings', 1)
        
        self.session_config_environment_variables.update({
            'admin_username': '_LIE_AUTH_USERNAME',
            'admin_email': '_LIE_USER_ADMIN_EMAIL',
            'admin_password': '_LIE_AUTH_PASSWORD'
        })

        self.oauth_client = oauth2.BackendApplicationClient('auth')

    def onInit(self, **kwargs):
        password_retrieval_message_file = os.path.join(self._config_dir, 'password_retrieval.txt')
        if os.path.isfile(password_retrieval_message_file):
            self._password_retrieval_message_template = open(password_retrieval_message_file).read()
        else:
            self._password_retrieval_message_template = PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE
            open(password_retrieval_message_file, 'w').write(self._password_retrieval_message_template)

        self.oauth_backend_server = oauth2.BackendApplicationServer(OAuthRequestValidator(self))
        self.db_lock = DeferredLock()

        self.autolog = False
        self.autoschema = False

        # TODO: check this before accessing the DB
        self.db_initialized = False

    @inlineCallbacks
    def onRun(self, details=None):
        # Subscribe DB initialization to the DB online event
        self.db_subscription = yield self.subscribe(self.init_admin_user, u'liestudio.db.events.online')

        
    @inlineCallbacks        
    def init_admin_user(self, event=None):
        # Acquire lock before initializing the database
        try:
            if not self.db_initialized:
                admin = yield self._get_user({'username': 'lieadmin'})
                if not admin:
                    self.log.info('Empty user table. Create default admin account')

                    userdata = {'username': self.session_config.get('admin_username', 'admin'),
                                'email': self.session_config.get('admin_email', None),
                                'password': hash_password(self.session_config.get('admin_password', None)),
                                'role': 'admin'}

                    admin = yield db.Model(self, 'users').insert_one(userdata)
                    
                    if not admin:
                        self.log.error('Unable to create default admin account')
                        self.leave('Unable to create default admin account, could not properly start.')

                    adminId = admin['ids'][0]

                    namespaces = yield db.Model(self, 'namespaces').insert_many([
                        {'userId': adminId, 'namespace': 'md'},
                        {'userId': adminId, 'namespace': 'atb'},
                        {'userId': adminId, 'namespace': 'docking'},
                        {'userId': adminId, 'namespace': 'structures'},
                        {'userId': adminId, 'namespace': 'logger'},
                        {'userId': adminId, 'namespace': 'config'}
                    ])

                # Cleanup previous run
                # Count number of active user sessions
                active_session_count = yield db.Model(self, 'sessions').count()
                self.log.info('{0} active user sessions'.format(active_session_count['total']))

                # Terminate active sessions
                if active_session_count:
                    deleted = yield db.Model(self, 'sessions').delete_many()
                    self.log.info('Terminate {0} active user sessions'.format(deleted["count"]))

                # Mark the database as initialized and unsubscribe
                self.db_initialized = True
        except Exception:
            pass

    def onExit(self, details=None):
        """
        User component exit routines

        Terminate all active sessions on component shutdown

        :param settings: global and module specific settings
        :type settings:  :py:class:`dict` or :py:class:`dict` like object
        :return:         successful exit sequence
        :rtype:          bool
        """

    @wamp.register(u'liestudio.auth.sso')
    @inlineCallbacks
    def user_sso(self, auth_token):
        """
        Handles Single Sign On by:
        - Verifing sso authentication token
        - Return user data

        :param auth_token: SSO authentication token
        :type auth_token:  int
        :return:           user data
        :rtype:            dict to JSON
        """

        self.log.debug("SSO authentication token recieved: {0}".format(auth_token))

        # TODO: We are prefilling the username here, need to write SSO auth
        # validation routine
        user = yield self._get_user('lieadmin')
        if self._validate_user_login(user, 'lieadmin', 'liepw@#'):
            user_settings = self._strip_unsafe_properties(user)
            user_settings['password'] = 'liepw@#'
            returnValue(user_settings)
        else:
            returnValue(False)

    @wamp.register(u'liestudio.auth.login')
    @inlineCallbacks
    def user_login(self, realm, authid, details):
        """
        Handles application authentication and authorization on the Crossbar
        WAMP session level by acting as the dynamic authorizer using any of
        the Crossbar supported authentication methods.

        For more information about crossbar authentication/authorization
        consult the online documentation at: http://crossbar.io/docs/Administration/

        This method also provides authentication based on IP/domain
        information in addition to the crossbar supported authentication
        methods.

        :param realm:   crossbar realm to connect to
        :type realm:    str
        :param authid:  authentication ID, usually username
        :type authid:   str
        :param details: additional details including authentication method
                        and transport details
        :type details:  :py:class:`dict`
        :return:        authentication response with the realm, user role and
                        user account info returned.
        :rtype:         :py:class:`dict` or False
        """

        authmethod = details.get(u'authmethod', None)

        # Resolve request domain
        domain = None
        if u'http_headers_received' in details:
            domain = details[u'http_headers_received'].get(u'host', None)
            details[u'domain'] = domain

        self.log.info('WAMP authentication request for realm: {realm}, authid: {authid}, method: {authmethod} domain: {domain}',
                       realm=realm, authid=authid, authmethod=authmethod, domain=domain)

        # Check for essentials (authid)
        if authid is None:
            raise ApplicationError('Authentication ID not defined')

        # Is the application only available for local users?
        if domain and self.package_config.get('only_localhost_access', False) and domain != 'localhost':
            raise ApplicationError('Access granted only to local users, access via domain {0}'.format(domain))

        # Is the domain blacklisted?
        if not ip_domain_based_access(domain, blacklist=self.package_config.get('domain-blacklist', [])):
            raise ApplicationError('Access from domain {0} not allowed'.format(domain))

        username = authid.strip()
        user = yield self._get_user(username)

        # WAMP-ticket authetication
        if authmethod == u'ticket':
            is_valid = self._validate_user_login(user, username, details['ticket'])
            if is_valid:
                auth_ticket = {u'realm': realm, u'role': user['role'], u'extra': self._strip_unsafe_properties(user)}
            else:
                client = yield self._get_client(username)
                if client:
                    http_basic = self._http_basic_authentication(username, details['ticket'])
                    credentials = {u'client': client, 
                                   u'http_basic': self._http_basic_authentication(client[u'clientId'], client[u'secret'])}
        
                    headers, body, status = self.oauth_backend_server.create_token_response(
                                                                        u'liestudio.auth.login',
                                                                        headers={u'Authorization': http_basic},
                                                                        grant_type_for_scope=u'client_credentials',
                                                                        credentials=credentials)

                    if status == 200:
                        user = {u'id': client[u'id']}
                        auth_ticket = {u'realm': realm, u'role': 'oauthclient', u'extra': {u'access_token': json.loads(body).get('accessToken')}}
                else:
                    raise ApplicationError("com.example.invalid_ticket", "could not authenticate session")

        # WAMP-CRA authentication
        elif authmethod == u'wampcra':
            if user:
                auth_ticket = {u'realm': realm, u'role': user['role'], u'extra': self._strip_unsafe_properties(user), 
                               u'secret': user[u'password']}
            else:
                raise ApplicationError("com.example.invalid_ticket", "could not authenticate session")

        else:
            raise ApplicationError("No such authentication method known: {0}".format(authmethod))

        yield self._start_session(user[u'id'], details.get(u'session', 0), auth_ticket[u'extra'].get('access_token'))
        
        # Log authorization
        self.log.info('Access granted. user: {user}', user=authid)

        returnValue(auth_ticket)

    @register(u'liestudio.auth.registerscopes', {}, {}, details_arg=True)
    def register_scopes(self, request, details):
        print(request, details)
        pass

    @wamp.register(u'liestudio.auth.authorize')
    @inlineCallbacks
    def authorize(self, session, uri, action, options):
        role = session.get('authrole')
                    
        if session.get('authprovider') is None and role in ('auth', 'schema', 'db', 'logger'):
            # Handle ring0 components
            
            # Allow full access on the role namespace
            if uri.startswith('liestudio.{}.'.format(role)):
                returnValue({'allow': True, 'disclose': True, 'cache': True})

            # Allow subscribe access on system events
            if re.match('liestudio\\.\\w+\\.events\\.\\w+', uri) and action == 'subscribe':
                returnValue({'allow': True, 'disclose': False, 'cache': True})

            # Allow retrieving namespaces for users
            if uri == u'liestudio.auth.namespaces' and action == 'call':
                returnValue({'allow': True, 'disclose': False, 'cache': True})

            # Allow retrieval of oauth client username
            if uri.startswith('liestudio.auth.oauth.client.getusername'):
                returnValue({'allow': True, 'disclose': False, 'cache': True})

            # Allow DB access and schema registration & retrieval
            if action == 'call':
                if re.match('liestudio\\.db\\.\\w+\\.{}'.format(role), uri) or uri == u'liestudio.schema.register.{}'.format(role):
                    returnValue({'allow': True, 'disclose': False})

                if uri == u'liestudio.schema.get':
                    returnValue({'allow': True, 'disclose': False})

            # Allow log publishing
            if action == 'publish' and uri == u'liestudio.logger.log.{}'.format(role):
                self.log.debug('DEBUG: authorizing {} to perform {} on {}'.format(role, action, uri))            
                returnValue({'allow': True, 'disclose': True})
        else:
            authid = session.get('authid')

            if role == 'oauthclient':
                client = yield self._get_client(authid)
                session = yield self._get_session(session.get('session'))
                namespaces = yield self.get_namespaces({'userId': client['userId']})

                def iter_scopes(pattern, **kwargs):
                    yield pattern.format(action=action, **kwargs)
                    yield pattern.format(action='*', **kwargs)
                
                ns = re.match('liestudio\\.(.+)\\..+', uri).group(1)

                scopes = itertools.chain(iter_scopes('{uri}:{action}', uri=uri), iter_scopes('ns.{ns}:{action}', ns=ns))

                # TODO: check custom scope name on uri
                scope_name = None

                if scope_name:
                    scopes = itertools.chain(scopes, iter_scopes('ns.{ns}.{scope}:{action}', ns=ns, scope=scope_name))
                
                headers = {'access_token': session['accessToken']}
                valid, r = self.oauth_backend_server.verify_request(uri, headers=headers, scopes=[scope for scope in scopes])

                valid = yield valid

                if valid:
                    returnValue({'allow': True, 'disclose': True, 'cache': True})

        # Allow admin to call, subscribe and publish on any uri
        if role == u'admin' and action in ('call', 'subscribe', 'publish'):
            returnValue({'allow': True, 'disclose': True})

        self.log.warn('WARNING: {} is not authorized for {} on {}'.format(authid, action, uri))

        returnValue(False)
    
    @wamp.register(u'liestudio.auth.namespaces')
    @inlineCallbacks
    def get_namespaces(self, request):
        if 'userId' in request:
            user_id = request['userId']
        else:
            user = yield self._get_user(request['username'].strip())
            
            if not user:
                returnValue([])

            user_id = user['id']


        namespaces = yield db.Model(self, 'namespaces').find_many({'userId': user_id})

        returnValue([n['namespace'] for n in namespaces['result']])

    @register(u'liestudio.auth.oauth.client.create', WampSchema('auth', 'oauth/client/client-request', 1), WampSchema('auth', 'oauth/client/client-response', 1), details_arg=True)
    @inlineCallbacks
    def create_oauth_client(self, request, details=None):
        user = yield self._get_user(details.caller_authid)

        clientInfo = copy.deepcopy(request)
        clientInfo['userId'] = user['id']
        clientInfo['clientId'] = generate_secret()
        clientInfo['secret'] = generate_secret()

        res = yield db.Model(self, 'clients').insert_one(clientInfo)

        returnValue({
            'id': clientInfo['clientId'],
            'secret': clientInfo['secret']
        })

    @register(u'liestudio.auth.oauth.client.getusername', {}, {})
    @inlineCallbacks
    def get_oauth_client_username(self, request, details=None):
        client = yield self._get_client(request['clientId'])

        if client:
            user = yield self._get_user({'id': client['userId']})

            returnValue({'username': user['username']})
        else:
            returnValue({})

    @register(u'liestudio.auth.oauth.client.authenticate', {}, {}, details_arg=True)
    @inlineCallbacks
    def grant_client_credentials(self, request):
        returnValue(self.oauth_backend_server.create_token_response(request['uri'], body=request['body']))
            
    @wamp.register(u'liestudio.auth.logout', options=wamp.RegisterOptions(details_arg='details'))
    @inlineCallbacks
    def user_logout(self, details):
        """
        Handles the user logout process by:
        - Retrieve user based on session_id

        :param session_id: user unique session ID
        :type session_id:  int
        """

        user = yield self._get_user(details.get('authid'))
        if user:
            self.log.info('Logout user: {0}, id: {1}'.format(user['username'], user['id']))

            ended = yield self._end_session(user['uid'], details.get('session'))
            if ended:
                returnValue('{0} you are now logged out'.format(user['username']))
    
        returnValue('Unknown user, unable to logout')

    @wamp.register(u'liestudio.auth.retrieve')
    def retrieve_password(self, email):
        """
        Retrieve a forgotten password by email
        This will reset the users password and
        send a temporary password by email.

        :param email: user account email
        """

        raise Exception

    # TODO: improve and register this method, with json schemas
    @inlineCallbacks
    def create_user(self, userdata, required=['username', 'email']):
        """
        Create new user and add to database
        """


        # TODO: handle the following section with json schema
        # ----------------------------------------------------------------------------
        user_template = copy.copy(USER_TEMPLATE)

        # Require at least a valid username and email
        for param in required:
            if not userdata.get(param, None):
                self.log.error('Unable to create new user. Missing "{0}"'.format(param))
                returnValue({})

        # If no password, create random one
        if not userdata.get('password', None):
            random_pw = generate_password()
            user_template['password'] = hash_password(random_pw)

        user_template.update(userdata)
        # ----------------------------------------------------------------------------

        # Username and email should not be in use
        user = yield self._get_user(userdata['username'])
        if user:
            self.log.error('Username {0} already in use'.format(userdata['username']))
            returnValue({})
        
        user = yield self._get_user({'email': userdata['email']})
        if user:
            self.log.error('Email {0} already in use'.format(userdata['email']))
            returnValue({})

        # Add the new user to the database
        result = yield db.Model(self, 'users').insert_one(user_template)
        if result:
            self.log.debug('Added new user. user: {username}, id: {id}', id=result['ids'][0], **user_template)
        else:
            self.log.error('Unable to add new user to database')
            returnValue({})

        returnValue(user_template)

    # TODO: expose and secure this
    def remove_user(self, userdata):
        """
        Remove a user from the database

        :param userdata: PyMongo style database query
        :type userdata:  :py:class:`dict`
        """

        user = self.get_user(userdata)
        if not user:
            logging.error('No such user to remove: {0}'.format(
                ' '.join(['{0},{1}'.format(*item) for item in userdata.items()])))
            return False
        else:
            logging.info('Removing user "{username}", with uid {uid} from database'.format(**user))
            db['users'].delete_one(user)

        return True

    def _validate_user_login(self, user, username, password):
        """
        Validate login attempt for user with password

        :param username: username to check
        :type username:  string
        :param password: password to check
        :type password:  string
        :rtype:          bool
        """

        password = password.strip()

        check = False
        if user:
            check = check_password(user['password'], password)
        else:
            self.log.debug('No such user')

        self.log.info('{status} login attempt for user: {user}',
            status='Correct' if check else 'Incorrect', user=username)

        return check

    @inlineCallbacks
    def _get_user(self, filter):
        if type(filter) is not dict:
            filter = {'username': filter}

        res = yield db.Model(self, 'users').find_one(filter)

        returnValue(res['result'])

    @inlineCallbacks
    def _get_client(self, client_id):
        client = yield db.Model(self, 'clients').find_one({'clientId': client_id})

        if client:
            returnValue(client['result'])
        else:
            returnValue(None)

    def _http_basic_authentication(self, username, password):
        # mimic HTTP basic authentication
        # concatenate username and password with a colon
        http_basic = u'{}:{}'.format(username, password)
        # encode into an octet sequence (bytes)
        http_basic = http_basic.encode('utf_8')
        # encode in base64
        http_basic = base64.encodebytes(http_basic)

        return http_basic.decode('utf_8')

    @inlineCallbacks
    def _start_session(self, user_id, session_id, access_token):
        self.log.debug('Open session: {0} for user {1}'.format(session_id, user_id))
        res = yield db.Model(self, 'sessions').insert_one({'userId': user_id, 'sessionId': session_id, 'accessToken': access_token})
        returnValue(res)

    @inlineCallbacks
    def _get_session(self, session_id):
        res = yield db.Model(self, 'sessions').find_one({'sessionId': session_id})
        returnValue(res['result'])

    @inlineCallbacks
    def _end_session(self, user_id, session_id):
        res = yield db.Model(self, 'sessions').delete_one({'userId': user_id, 'sessionId': session_id})
        returnValue(res['count'] > 0)

    def _strip_unsafe_properties(self, _user):
        user = _user.copy()

        for entry in self.package_config.get('unsafe_properties'):
            if entry in user:
                del user[entry]
        
        return user

    @inlineCallbacks
    def _retrieve_password(self, email):
        """
        Retrieve password by email
        
        The email message template for user account password retrieval
        is stored in the self._password_retrieval_message_template variable.
        
        * Locates the user in the database by email which should be a 
          unique and persistent identifier.
        * Generate a new random password
        * Send the new password to the users email once. If the email
          could not be send, abort the procedure
        * Save the new password in the database.
        
        :param email: email address to search user for
        :type email:  string
        """

        user = yield self._get_user({'email': email})
        if not user:
          self.log.info('No user with email {0}'.format(email))
          return

        new_password = generate_password()
        user['password'] = hash_password(new_password)
        self.log.debug('New password {0} for user {1} send to {2}'.format(new_password, user, email))

        with Email() as email:
          email.send(
            email,
            self._password_retrieval_message_template.format(password=new_password, user=user['username']),
            'Password retrieval request for LIEStudio'
          )
          res = yield db.Model(self, 'users').update_one({'id': user['id']}, {'password': new_password})

        returnValue(user)
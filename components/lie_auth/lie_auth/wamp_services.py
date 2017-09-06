# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import re
import copy
import json
import pytz
import base64
import datetime
import itertools

from autobahn import wamp
from autobahn.wamp.exception import ApplicationError
from autobahn.twisted.util import sleep
from twisted.logger import Logger
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from oauthlib import oauth2
from oauthlib.common import Request as OAuthRequest, generate_client_id as generate_secret
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from mdstudio import BaseApplicationSession, WampSchema, register
from mdstudio.db.model import Model
from .util import check_password, hash_password, ip_domain_based_access, generate_password
from .password_retrieval import PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE
from .oauth.request_validator import OAuthRequestValidator
from .authorizer import Authorizer

class AuthWampApi(BaseApplicationSession):
    """
    User management WAMP methods.
    """

    log = Logger()

    def preInit(self, **kwargs):
        self.session_config_template = WampSchema('auth', 'session_config/session_config')
        self.package_config_template = WampSchema('auth', 'settings/settings')
        
        self.session_config_environment_variables.update({
            'admin_username': '_LIE_AUTH_USERNAME',
            'admin_email': '_LIE_USER_ADMIN_EMAIL',
            'admin_password': '_LIE_AUTH_PASSWORD'
        })

        self.oauth_client = oauth2.BackendApplicationClient('auth')
        self.session_config['loggernamespace'] = 'auth'

    def onInit(self, **kwargs):
        password_retrieval_message_file = os.path.join(self._config_dir, 'password_retrieval.txt')
        if os.path.isfile(password_retrieval_message_file):
            self._password_retrieval_message_template = open(password_retrieval_message_file).read()
        else:
            self._password_retrieval_message_template = PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE
            open(password_retrieval_message_file, 'w').write(self._password_retrieval_message_template)

        self.oauth_backend_server = oauth2.BackendApplicationServer(OAuthRequestValidator(self))

        self.autolog = False
        self.autoschema = False

        # TODO: check this before accessing the DB
        self.db_initialized = False

        self.authorizer = Authorizer()
        
        # # TODO: make this a dict of  {vendor}.{namespace}: [urilist] for faster lookup
        # self.registrations = []

    @inlineCallbacks
    def onRun(self, details=None):
        # Subscribe DB initialization to the DB online event
        yield DBWaiter(self, self.init_admin_user).run()

        # yield sleep(5)
        # subs = yield self.call(u'wamp.subscription.list')
        # print(subs)

        # @inlineCallbacks
        # def sub_info(id):
        #     sub = yield self.call(u'wamp.subscription.get', id)
        #     print(sub)
        #     count = yield self.call(u'wamp.subscription.list_subscribers', id)
        #     print(count)

        # for id in itertools.chain(subs['exact'], subs['prefix'], subs['wildcard']):
        #     yield sub_info(id)

        # @inlineCallbacks
        # def reg_info(id):
        #     reg = yield self.call(u'wamp.registration.get', id)
        #     print(reg)
        #     count = yield self.call(u'wamp.registration.list_callees', id)
        #     print(count)

        # regs = yield self.call(u'wamp.registration.list')
        # print(regs)

        # for id in itertools.chain(regs['exact'], regs['prefix'], regs['wildcard']):
        #     yield reg_info(id)

        
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

                    admin = yield Model(self, 'users').insert_one(userdata)
                    
                    if not admin:
                        self.log.error('Unable to create default admin account')
                        self.leave('Unable to create default admin account, could not properly start.')

                    adminId = admin

                    namespaces = yield Model(self, 'namespaces').insert_many([
                        {'userId': adminId, 'namespace': 'md'},
                        {'userId': adminId, 'namespace': 'atb'},
                        {'userId': adminId, 'namespace': 'docking'},
                        {'userId': adminId, 'namespace': 'structures'},
                        {'userId': adminId, 'namespace': 'config'}
                    ])

                # Cleanup previous run
                # Count number of active user sessions
                active_session_count = yield Model(self, 'sessions').count()
                self.log.info('{0} active user sessions'.format(active_session_count))

                # Terminate active sessions
                if active_session_count:
                    deleted = yield Model(self, 'sessions').delete_many()
                    self.log.info('Terminate {0} active user sessions'.format(deleted))

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

    @wamp.register(u'mdstudio.auth.sso')
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

    @wamp.register(u'mdstudio.auth.login')
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
                # Not a valid user, try  to find a matching client
                client = yield self._get_client(username)
                if client:
                    http_basic = self._http_basic_authentication(username, details['ticket'])
                    credentials = {u'client': client, 
                                   u'http_basic': self._http_basic_authentication(client[u'clientId'], client[u'secret'])}
        
                    headers, body, status = self.oauth_backend_server.create_token_response(
                                                                        u'mdstudio.auth.login',
                                                                        headers={u'Authorization': http_basic},
                                                                        grant_type_for_scope=u'client_credentials',
                                                                        credentials=credentials)

                    if status == 200:
                        user = {u'id': client[u'_id']}
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

        yield self._start_session(user[u'_id'], details.get(u'session', 0), auth_ticket[u'extra'].get('access_token'))
        
        # Log authorization
        self.log.info('Access granted. user: {user}', user=authid)

        returnValue(auth_ticket)

    @register(u'mdstudio.auth.oauth.registerscopes', {}, {}, match='prefix')
    @inlineCallbacks
    def register_scopes(self, request):
        for scope in request['scopes']:
            # update/insert the uri scope
            yield Model(self, 'scopes').update_one(scope, {'$set': scope}, True)

        returnValue(None)
            
    @wamp.register(u'mdstudio.auth.authorize.admin')
    def authorize_admin(self, session, uri, action, options):
        role = session.get('authrole')
        
        authorization = False

        if action in ('call', 'subscribe', 'publish'):
            # Allow admin to call, subscribe and publish on any uri
            # TODO: possibly restrict this
            authorization = {'allow': True}

        if not authorization:
            self.log.warn('WARNING: {} is not authorized for {} on {}'.format(authid, action, uri))
        else:
            if 'disclose' not in authorization:
                authorization['disclose'] = False

            self._store_action(uri, action, options)

        return authorization
            
    @wamp.register(u'mdstudio.auth.authorize.ring0')
    def authorize_ring0(self, session, uri, action, options):
        role = session.get('authrole')
        
        authorization = self.authorizer.authorize_ring0(uri, action, role)        

        if not authorization:
            self.log.warn('WARNING: {} is not authorized for {} on {}'.format(role, action, uri))
        else:
            if 'disclose' not in authorization:
                authorization['disclose'] = False

            self._store_action(uri, action, options)

        return authorization
            

    @wamp.register(u'mdstudio.auth.authorize.oauth')
    @inlineCallbacks
    def authorize_oauth(self, session, uri, action, options):
        role = session.get('authrole')

        authid = session.get('authid')

        authorization = False

        client = yield self._get_client(authid)
        session = yield self._get_session(session.get('session'))
        scopes = self.authorizer.oauthclient_scopes(uri, action, authid)
        
        headers = {'access_token': session['accessToken']}
        valid, r = self.oauth_backend_server.verify_request(uri, headers=headers, scopes=[scope for scope in scopes])

        valid = yield valid

        if valid:
            authorization = {'allow': True}

        if not authorization:
            self.log.warn('WARNING: {} is not authorized for {} on {}'.format(authid, action, uri))
        else:
            if 'disclose' not in authorization:
                authorization['disclose'] = False

            self._store_action(uri, action, options)

        returnValue(authorization)
            
    @wamp.register(u'mdstudio.auth.authorize.public')
    def authorize_public(self, session, uri, action, options):
        #  TODO: authorize public to view unprotected resources
        authorization = False

        returnValue(authorization)
            
    @wamp.register(u'mdstudio.auth.authorize.user')
    def authorize_user(self, session, uri, action, options):
        # TODO: authorize users to view (parts of) the web interface and to create OAuth clients on their group/user
        authorization = False

        returnValue(authorization)

    @register(u'mdstudio.auth.oauth.client.create', WampSchema('auth', 'oauth/client/client-request'), WampSchema('auth', 'oauth/client/client-response'), details_arg=True)
    @inlineCallbacks
    def create_oauth_client(self, request, details=None):
        user = yield self._get_user(details.caller_authid)

        # TODO: check if user is permitted to access the requested scopes before creating the client
        clientInfo = copy.deepcopy(request)
        clientInfo['userId'] = user['_id']
        clientInfo['clientId'] = generate_secret()
        clientInfo['secret'] = generate_secret()

        res = yield Model(self, 'clients').insert_one(clientInfo)

        returnValue({
            'id': clientInfo['clientId'],
            'secret': clientInfo['secret']
        })

    @register(u'mdstudio.auth.oauth.client.getusername', {}, {})
    @inlineCallbacks
    def get_oauth_client_username(self, request, details=None):
        client = yield self._get_client(request['clientId'])

        if client:
            user = yield self._get_user({'id': client['userId']})

            returnValue({'username': user['username']})
        else:
            returnValue({})
            
    @wamp.register(u'mdstudio.auth.logout', options=wamp.RegisterOptions(details_arg='details'))
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
            self.log.info('Logout user: {0}, id: {1}'.format(user['username'], user['_id']))

            ended = yield self._end_session(user['uid'], details.get('session'))
            if ended:
                returnValue('{0} you are now logged out'.format(user['username']))
    
        returnValue('Unknown user, unable to logout')

    @wamp.register(u'mdstudio.auth.retrieve')
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
        result = yield Model(self, 'users').insert_one(user_template)
        if result:
            self.log.debug('Added new user. user: {username}, id: {id}', id=result, **user_template)
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

        res = yield Model(self, 'users').find_one(filter)

        returnValue(res)

    @inlineCallbacks
    def _get_client(self, client_id):
        client = yield Model(self, 'clients').find_one({'clientId': client_id})

        if client:
            returnValue(client)
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
        res = yield Model(self, 'sessions').insert_one({'userId': user_id, 'sessionId': session_id, 'accessToken': access_token})
        returnValue(res)

    @inlineCallbacks
    def _get_session(self, session_id):
        res = yield Model(self, 'sessions').find_one({'sessionId': session_id})
        returnValue(res)

    @inlineCallbacks
    def _end_session(self, user_id, session_id):
        res = yield Model(self, 'sessions').delete_one({'userId': user_id, 'sessionId': session_id})
        returnValue(res > 0)

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
          res = yield Model(self, 'users').update_one({'id': user['_id']}, {'password': new_password})

        returnValue(user)

    def _store_action(self, uri, action, options):
        registration = Model(self, 'registration_info')

        now = datetime.datetime.now(pytz.utc).isoformat()

        if action == 'register':
            match = options.get('match', 'exact')

            @inlineCallbacks
            def update_registration():
                upd = yield registration.update_one(
                    {
                        'uri': uri,
                        'match': match
                    }, 
                    {
                        '$inc': {
                            'registrationCount': 1
                        },
                        '$set': {
                            'latestRegistration': now
                        },
                        '$setOnInsert': {
                            'uri': uri,
                            'firstRegistration': now,
                            'match': match
                        }
                    }, 
                    upsert=True, 
                    date_fields=['update.$set.latestRegistration', 'update.$setOnInsert.firstRegistration']
                )
                
            # We cannot be sure the DB is already up, possibly wait
            yield DBWaiter(self, update_registration).run()
        elif action == 'call':
            @inlineCallbacks
            def update_registration():
                id = yield self.call(u'wamp.registration.match', uri)
                if id:
                    reg_info = yield self.call(u'wamp.registration.get', id)
                    yield registration.update_one(
                        {
                            'uri': reg_info['uri'],
                            'match': reg_info['match']
                        },
                        {
                            '$inc': {
                                'callCount': 1
                            },
                            '$set': {
                                'latestCall': now
                            }
                        },
                        date_fields=['update.$set.latestCall']
                    )

            # We cannot be sure the DB is already up, possibly wait
            yield DBWaiter(self, update_registration).run()

class DBWaiter:
    def __init__(self, session, callback):
        self.session = session
        self.callback = callback
        self.unsub = Deferred()
        self.called = False
        self.sub = None

        self.unsub.addCallback(self._unsubscribe)

    @inlineCallbacks
    def run(self):
        if not self.session.db_initialized:
            self.sub = yield self.session.subscribe(self._callback_wrapper, u'mdstudio.db.events.online')

            reactor.callLater(0.25, self._check_called)
        else:
            yield self.callback()
            self.called = True

    @inlineCallbacks
    def _callback_wrapper(self, event):
        yield self.callback()
        self.called = True
        self.unsub.callback(True)
        self.session.db_initialized = True

    def _unsubscribe(self, event=None):
        self.sub.unsubscribe()

    def _check_called(self):
        if self.session.db_initialized:
            if not self.called:
                self._callback_wrapper(True)
        else:
            reactor.callLater(0.25, self._check_called)

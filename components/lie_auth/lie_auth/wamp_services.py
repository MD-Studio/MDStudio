# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os
import re

from autobahn import wamp
from autobahn.wamp.exception import ApplicationError
from twisted.logger import Logger
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock
from oauthlib import oauth2
from oauthlib.common import Request as OAuthRequest

from lie_componentbase import BaseApplicationSession, WampSchema, register
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

        # TODO: check this before accessing the DB
        self.db_initialized = False

    @inlineCallbacks
    def onRun(self, details=None):
        # Subscribe DB initialization to the DB online event
        self.db_subscription = yield self.subscribe(self.init_admin_user, u'liestudio.db.events.online', options=wamp.SubscribeOptions(match="exact"))

        try:
            status = yield self.call(u'liestudio.db.status')
        except Exception:
            status = False

        # If the DB is already online, initialize it now and unsubscribe
        if status:
            self.init_admin_user()

        
    @inlineCallbacks        
    def init_admin_user(self, event=None):
        # Acquire lock before initializing the database
        yield self.db_lock.acquire()

        try:
            if not self.db_initialized:
                admin = yield self._get_user({'username': 'lieadmin'})
                if not admin:
                    self.log.info('Empty user table. Create default admin account')

                    userdata = {'username': self.session_config.get('admin_username', 'admin'),
                                'email': self.session_config.get('admin_email', None),
                                'password': hash_password(self.session_config.get('admin_password', None)),
                                'role': 'admin'}

                    admin = yield self.call(u'liestudio.db.insertone', {'collection': 'users', 'insert': userdata})

                    adminId = admin['ids'][0]

                    namespaces = yield self.call(u'liestudio.db.insertmany', {
                        'collection': 'namespaces',
                        'insert': [
                            {'userId': adminId, 'namespace': 'md'},
                            {'userId': adminId, 'namespace': 'atb'},
                            {'userId': adminId, 'namespace': 'docking'},
                            {'userId': adminId, 'namespace': 'structures'},
                            {'userId': adminId, 'namespace': 'logger'},
                            {'userId': adminId, 'namespace': 'config'}
                        ]
                    })
                    if not admin:
                        self.log.error('Unable to create default admin account')
                        self.leave('Unable to create default admin account, could not properly start.')

                # Cleanup previous run
                # Count number of active user sessions
                active_session_count = yield self.call(u'liestudio.db.count', {'collection': 'sessions', 'filter': {}}) 
                self.log.info('{0} active user sessions'.format(active_session_count['total']))

                # Terminate active sessions
                if active_session_count:
                    deleted = yield self.call(u'liestudio.db.deletemany', {'collection': 'sessions', 'filter': {}})
                    self.log.info('Terminate {0} active user sessions'.format(deleted["count"]))

                # Mark the database as initialized and unsubscribe
                self.db_initialized = True
                yield self.db_subscription.unsubscribe()
        except Exception:
            pass

        self.db_lock.release()

    @inlineCallbacks
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
                raise ApplicationError("com.example.invalid_ticket", "could not authenticate session")

        # WAMP-CRA authentication
        elif authmethod == u'wampcra':
            if user:
                auth_ticket = {u'realm': realm, u'role': user['role'], u'extra': self._strip_unsafe_properties(user), 
                               u'secret': user['password']}
            else:
                raise ApplicationError("com.example.invalid_ticket", "could not authenticate session")

        else:
            raise ApplicationError("No such authentication method known: {0}".format(authmethod))

        self._start_session(user['id'], details.get(u'session', 0))
        
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

        if role and role in PERMISSIONS.keys():
            for rule in PERMISSIONS[role]:
                rulematch = False
                if 'match' in rule.keys():
                    if rule['match'] == 'prefix' and uri.startswith('{}.'.format(rule['uri'])):
                        rulematch = True
                    elif rule['match'] == 'exact' and uri == rule['uri']:
                        rulematch = True
                
                if rulematch:
                    permission = extract_permission(rule, uri, action)
                    self.log.debug( 'DEBUG: found matching rule {rule}, permission is: {permission}', rule=rule, permission=permission)
                    returnValue(permission)
                    
        if session.get('authprovider') is None and role in ('auth', 'schema', 'db'):
            authid = role

            if uri.startswith('liestudio.{}.'.format(authid)):
                returnValue({'allow': True, 'disclose': False, 'cache': True})

            if uri == u'wamp.subscription.get_events':
                returnValue({'allow': True, 'disclose': False, 'cache': True})
        else:
            authid = session.get('authid')
            namespaces = yield self.get_namespaces({'username': authid})

            if namespaces and any([uri.startswith('liestudio.{}.'.format(namespace)) for namespace in namespaces]):
                self.log.debug('DEBUG: authorizing {} to perform {} on {}'.format(authid, action, uri))
                returnValue({'allow': True, 'disclose': True})

        self.log.debug( 'DEBUG: authid resoved to {}'.format(authid))
        if authid and action == 'call' and (uri.startswith('liestudio.db.') or uri == u'liestudio.schema.register'):
            self.log.debug('DEBUG: authorizing {} to perform {} on {}'.format(authid, action, uri))
            returnValue({'allow': True, 'disclose': True})

        if action == 'call' and re.match('liestudio.schema.get', uri):
            self.log.debug('DEBUG: authorizing {} to perform {} on {}'.format(authid, action, uri))
            returnValue({'allow': True, 'disclose': False})

        if action == 'call' and uri == u'liestudio.auth.logout':
            self.log.debug('DEBUG: authorizing {} to perform {} on {}'.format(authid, action, uri))            
            returnValue({'allow': True, 'disclose': True})

        if authid and action == 'publish' and uri == u'liestudio.logger.log':
            self.log.debug('DEBUG: authorizing {} to perform {} on {}'.format(authid, action, uri))            
            returnValue({'allow': True, 'disclose': True})

        if authid == u'lieadmin' and action == 'call' and uri == u'wamp.subscription.get_events':
            returnValue({'allow': True, 'disclose': False})

        self.log.warn('WARNING: {} is not authorized for {} on {}'.format(authid, action, uri))

        returnValue(False)
    
    @wamp.register(u'liestudio.auth.namespaces')
    @inlineCallbacks
    def get_namespaces(self, request):
        user = yield self._get_user(request['username'].strip())
        namespaces = yield self.call(u'liestudio.db.findmany', {'collection': 'namespaces', 'filter': {'userId': user['id']}})

        returnValue([n['namespace'] for n in namespaces['result']])
            
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
        result = yield self.call(u'liestudio.db.insertone', {'collection': 'users', 'insert': user_template})
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

        res = yield self.call(u'liestudio.db.findone', {'collection': 'users', 'filter': filter})

        returnValue(res['result'])

    def _start_session(self, user_id, session_id):
        self.log.debug('Open session: {0} for user {1}'.format(session_id, user_id))
        yield self.call(u'liestudio.db.insertone', {'collection': 'sessions', 'insert': {'userId': user_id, 'session_id': session_id}})

    @inlineCallbacks
    def _end_session(self, user_id, session_id):
        res = yield self.call(u'liestudio.db.deleteone', {'collection': 'sessions', 'filter': {'userId': user_id, 'session_id': session_id}})
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
          res = yield self.call(u'liestudio.db.updateone', {'collection': 'users', 'filter': {'_id': user['_id']}, 'update': {'password': new_password}})

        returnValue(user)

# TODO: convert to fully dynamic permissions
PERMISSIONS = {
    "public": [
        {
            "uri": u"liestudio.public",
            "match": "prefix",
            "allow": {
                "call": True,
                "register": False,
                "publish": False,
                "subscribe": True
            },
            "disclose": {
                "caller": False,
                "publisher": False
            },
            "cache": True
        }
    ],
    "auth": [
        {
            "uri": u"liestudio.auth",
            "match": "prefix",
            "allow": {
                "call": False,
                "register": True,
                "publish": False,
                "subscribe": False
            },
            "disclose": {
                "caller": False,
                "publisher": False
            },
            "cache": False
        }
    ],
    "db": [
        {
            "uri": u"liestudio.auth.namespaces",
            "match": "exact",
            "allow": {
                "call": True,
                "register": False,
                "publish": False,
                "subscribe": False
            },
            "disclose": {
                "caller": False,
                "publisher": False
            },
            "cache": True
        }
    ],
    "schema": [
        {
            "uri": u"liestudio.schema",
            "match": "prefix",
            "allow": {
                "call": True,
                "register": True,
                "publish": False,
                "subscribe": False
            },
            "disclose": {
                "caller": True,
                "publisher": True
            },
            "cache": True
        }
    ]
}

def extract_permission(rule, uri, action):
    if type(rule['allow']) is dict:
        permission = {}
        if rule['allow'].get(action):
            permission['allow'] = True
            permission['cache'] = rule.get('cache')

            if type(rule['disclose']) is dict and rule['disclose'].get('{}er'.format(action)):
                permission['disclose'] = True
            else:
                permission['disclose'] = False
        
            return permission
    else:
        return rule['allow']

    return False
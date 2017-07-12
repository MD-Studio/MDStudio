# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import os

from autobahn import wamp
from autobahn.wamp.exception import ApplicationError
from twisted.logger import Logger
from twisted.internet.defer import inlineCallbacks, returnValue

from lie_componentbase import BaseApplicationSession, WampSchema
from .util import check_password, hash_password, ip_domain_based_access, generate_password
from .password_retrieval import PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE

logger = Logger()


class UserWampApi(BaseApplicationSession):
    """
    User management WAMP methods.
    """

    def preInit(self, **kwargs):
        self.session_config_template = WampSchema('user', 'session_config', 1)
        self.package_config_template = WampSchema('user', 'settings', 1)
        
        self.session_config_environment_variables.update({
            'admin_username': '_LIE_AUTH_USERNAME',
            'admin_email': '_LIE_USER_ADMIN_EMAIL',
            'admin_password': '_LIE_AUTH_PASSWORD'
        })

    def onInit(self, **kwargs):
        password_retrieval_message_file = os.path.join(self._config_dir, 'password_retrieval.txt')
        if os.path.isfile(password_retrieval_message_file):
            self._password_retrieval_message_template = open(password_retrieval_message_file).read()
        else:
            self._password_retrieval_message_template = PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE
            open(password_retrieval_message_file, 'w').write(self._password_retrieval_message_template)

    @inlineCallbacks
    def onRun(self, details=None):
        admin = yield self._get_user({'uid': 0})
        if not admin:
            logger.info('Empty user table. Create default admin account')

            userdata = {'username': self.session_config.get('admin_username', 'admin'),
                        'email': self.session_config.get('admin_email', None),
                        'password': hash_password(self.session_config.get('admin_password', None)),
                        'role': 'admin',
                        'uid': 0}

            admin = yield self.call(u'liestudio.db.insert', {'collection': 'users', 'query': {'document': userdata}})
            namespaces = yield self.call(u'liestudio.db.insertmany', {
                'collection': 'namespaces',
                'query': {
                    'documents': [
                        {'uid': 0, 'namespace': 'md'},
                        {'uid': 0, 'namespace': 'atb'},
                        {'uid': 0, 'namespace': 'docking'},
                        {'uid': 0, 'namespace': 'structures'},
                        {'uid': 0, 'namespace': 'logger'},
                        {'uid': 0, 'namespace': 'config'}
                    ]
                }
            })
            if not admin:
                logger.error('Unable to create default admin account')
                self.leave('Unable to create default admin account, could not properly start.')

        # Cleanup after improper shutdown
        status = yield self.onExit()

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

        # Count number of active user sessions
        active_session_count = yield self.call(u'liestudio.db.count', {'collection': 'sessions', 'query': {}}) 
        logger.info('{0} active user sessions'.format(active_session_count))

        # Terminate active sessions
        if active_session_count:
            deleted = yield self.call(u'liestudio.db.deletemany', {'collection': 'sessions', 'query': {'filter': {}}})
            logger.info('Terminate {0} active user sessions'.format(deleted["deleted_count"]))

        returnValue(True)

    @wamp.register(u'liestudio.user.sso')
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

    @wamp.register(u'liestudio.user.login')
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

        self._start_session(user['uid'], details.get(u'session', 0))
        
        # Log authorization
        self.log.info('Access granted. user: {user}', user=authid, **details)

        returnValue(auth_ticket)
    
    @wamp.register(u'liestudio.user.namespaces')
    @inlineCallbacks
    def get_namespaces(self, request):
        user = yield self._get_user(request['username'].strip())
        namespaces = yield self.call(u'liestudio.db.findmany', {'collection': 'namespaces', 'query': {'filter': {'uid': user['uid']}}})

        returnValue([n['namespace'] for n in namespaces])
            
    @wamp.register(u'liestudio.user.logout', options=wamp.RegisterOptions(details_arg='details'))
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
            logger.info('Logout user: {0}, uid: {1}'.format(self.user['username'], self.user['uid']))

            ended = yield self._end_session(user['uid'], details.get('session'))
            if ended:
                returnValue('{0} you are now logged out'.format(user['username']))
    
        returnValue('Unknown user, unable to logout')

    @wamp.register(u'liestudio.user.retrieve')
    def retrieve_password(self, email):
        """
        Retrieve a forgotten password by email
        This will reset the users password and
        send a temporary password by email.

        :param email: user account email
        """

        return self.usermanager.retrieve_password(email)

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
                logger.error('Unable to create new user. Missing "{0}"'.format(param))
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
            logger.error('Username {0} already in use'.format(userdata['username']))
            returnValue({})
        
        user = yield self._get_user({'email': userdata['email']})
        if user:
            logger.error('Email {0} already in use'.format(userdata['email']))
            returnValue({})

        # Make new uid, increment max uid by 0
        uid = yield self.call(u'liestudio.db.find', {'collection': 'users', 'query': {'sort': [['uid', -1]]}})
        if not uid:
            uid = 0
        else:
            uid = uid['uid']
            uid += 1
        user_template['uid'] = uid

        # Add the new user to the database
        did = yield self.call(u'liestudio.db.insert', {'collection': 'users', 'query': {'document': user_template}})
        if did:
            logger.debug('Added new user to database. user: {username}, uid: {uid}'.format(**user_template))
        else:
            logger.error('Unable to add new user to database')
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
            logger.debug('No such user')

        logger.info('{status} login attempt for user: {user}',
            status='Correct' if check else 'Incorrect', user=username)

        return check

    @inlineCallbacks
    def _get_user(self, filter):
        if type(filter) is not dict:
            filter = {'username': filter}

        res = yield self.call(u'liestudio.db.find', {'collection': 'users', 'query': {'filter': filter}})

        returnValue(res)

    def _start_session(self, uid, session_id):
        logger.debug('Open session: {0} for user {1}'.format(session_id, uid))
        self.call(u'liestudio.db.insert', {'collection': 'sessions', 'query': {'document': {'uid': uid, 'session_id': session_id}}})

    @inlineCallbacks
    def _end_session(self, uid, session_id):
        res = yield self.call(u'liestudio.db.delete', {'collection': 'sessions', 'query': {'filter': {'uid': uid, 'session_id': session_id}}})
        returnValue(res['deleted_count'] > 0)

    def _strip_unsafe_properties(self, _user):
        user = _user.copy()

        for entry in self.package_config.get('unsafe_properties'):
            if entry in user:
                del user[entry]
        
        returnValue(user)

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
          logger.info('No user with email {0}'.format(email))
          return

        new_password = generate_password()
        user['password'] = hash_password(new_password)
        logger.debug('New password {0} for user {1} send to {2}'.format(new_password, user, email))

        with Email() as email:
          email.send(
            email,
            self._password_retrieval_message_template.format(password=new_password, user=user['username']),
            'Password retrieval request for LIEStudio'
          )
          res = yield self.call(u'liestudio.db.update', {'collection': 'users', 'query': {'filter': {'_id': user['_id']}, 'update': {'password': new_password}}})

        returnValue(user)

def make(config):
    """
    Component factory

    This component factory creates instances of the application component
    to run.

    The function will get called either during development using an
    ApplicationRunner, or as a plugin hosted in a WAMPlet container such as
    a Crossbar.io worker.
    The BaseApplicationSession class is initiated with an instance of the
    ComponentConfig class by default but any class specific keyword arguments
    can be consument as well to populate the class session_config and
    package_config dictionaries.

    :param config: Autobahn ComponentConfig object
    """

    if config:
        return UserWampApi(config, package_config=SETTINGS)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio user management WAMPlet',
                'description': 'WAMPlet proving LIEStudio user management endpoints'}

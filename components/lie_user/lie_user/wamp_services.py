# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

from autobahn import wamp
from autobahn.wamp.exception import ApplicationError

from lie_componentbase import BaseApplicationSession
from management import UserManager, resolve_domain, ip_domain_based_access
from settings import SETTINGS


class UserWampApi(BaseApplicationSession):
    """
    User management WAMP methods.
    """

    def __init__(self, config, **kwargs):
        BaseApplicationSession.__init__(self, config, **kwargs)
        self.usermanager = UserManager()

    @wamp.register(u'liestudio.user.sso')
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
        if self.usermanager.validate_user_login('lieadmin', 'liepw@#'):
            user_settings = self.usermanager.get_safe_user({'username': 'lieadmin'})
            user_settings['password'] = 'liepw@#'
            return user_settings
        else:
            return False

    @wamp.register(u'liestudio.user.login')
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

        self.log.debug('WAMP authentication request for realm: {realm}, authid: {authid}, method: {authmethod} domain: {domain}',
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

        # WAMP-ticket authetication
        if authmethod == u'ticket':
            if self.usermanager.validate_user_login(authid, details['ticket']):
                self.usermanager.set_session_id(details.get(u'session', 0))
                user_settings = self.usermanager.get_safe_user({'username': authid})
                auth_ticket = {u'realm': realm, u'role': user_settings['role'], u'extra': user_settings}
            else:
                raise ApplicationError("com.example.invalid_ticket", "could not authenticate session")

        # WAMP-CRA authentication
        elif authmethod == u'wampcra':
            self.usermanager.set_session_id(details.get(u'session', 0))
            user_settings = self.usermanager.get_user({'username': authid})
            if user_settings:
                auth_ticket = {u'realm': realm, u'role': user_settings['role'], u'extra': user_settings,
                               u'secret': user_settings['password']}
            else:
                raise ApplicationError("com.example.invalid_ticket", "could not authenticate session")

        else:
            raise ApplicationError("No such authentication method known: {0}".format(authmethod))

        # Log authorization
        self.log.info('Access granted. user: {user}', user=authid, **details)

        return auth_ticket

    @wamp.register(u'liestudio.user.logout')
    def user_logout(self, session_id):
        """
        Handles the user logout process by:
        - Retrieve user based on session_id

        :param session_id: user unique session ID
        :type session_id:  int
        """

        user = self.usermanager.get_user({'session_id': str(session_id)})
        if self.usermanager.user:
            if self.usermanager.user_logout():
                return '{0} you are now logged out'.format(user['username'])

        return 'Unknown user, unable to logout'

    @wamp.register(u'liestudio.user.retrieve')
    def retrieve_password(self, email):
        """
        Retrieve a forgotten password by email
        This will reset the users password and
        send a temporary password by email.

        :param email: user account email
        """

        return self.usermanager.retrieve_password(email)


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

# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

from autobahn import wamp
from pymongo import MongoClient
from twisted.internet.defer import inlineCallbacks

from lie_system import LieApplicationSession
from management import UserManager

class UserWampApi(LieApplicationSession):
    """
    User management WAMP methods.
    """
    
    def __init__(self, config, **kwargs):
        LieApplicationSession.__init__(self, config, **kwargs)
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
        
        self.logging.debug("SSO authentication token recieved: {0}".format(auth_token))
        
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
        Handles the user login process by:
        - Verify user credentials
        - Initiate a new user session
        - Return user data

        :param username: username
        :type username:  str
        :param password: password
        :type password:  str
        :return:         user data
        :rtype:          dict to JSON
        """
        
        print("WAMP-Ticket dynamic authenticator invoked: realm='{0}', authid='{1}', details={2}".format(realm, authid, details))
        return {'secret': 'secret2', 'role': 'public'}
        
        
        if self.usermanager.validate_user_login(username, password):
            self.usermanager.set_session_key()
            user_settings = self.usermanager.get_safe_user({'username': username})
            return user_settings
        else:
            return False

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
  
    This component factory creates instances of the
    application component to run.
    
    The function will get called either during development
    using the ApplicationRunner below, or as  a plugin running
    hosted in a WAMPlet container such as a Crossbar.io worker.
    """
    if config:
        return UserWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio user management WAMPlet',
                'description': 'WAMPlet proving LIEStudio user management endpoints'}
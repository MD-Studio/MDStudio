# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from pymongo import MongoClient
from twisted.logger import Logger, LogLevel
from twisted.internet.defer import inlineCallbacks

from .management import UserManager

class UserWampApi(ApplicationSession):
    """
    User management WAMP methods.
    """
    
    logging = Logger()

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
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
    def user_login(self, username, password):
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

    @inlineCallbacks
    def onJoin(self, details):
        res = yield self.register(self)
        self.logging.debug("UserBackend: {0} procedures registered!".format(len(res)))

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

if __name__ == '__main__':
    
    # test drive the component during development ..
    runner = ApplicationRunner(
        url="wss://localhost:8083/ws",
        realm="liestudio")

    runner.run(make)
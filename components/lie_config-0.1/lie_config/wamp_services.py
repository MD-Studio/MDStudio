# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

import time

from   twisted import logger 
from   twisted.internet.defer import inlineCallbacks
from   autobahn               import wamp
from   autobahn.twisted.wamp  import ApplicationSession

# from settings               import SETTINGS

class ConfigBackend(ApplicationSession):

  def __init__(self, config):
    ApplicationSession.__init__(self, config)
    self.config = []
  
  @wamp.register(u'liestudio.config.get')
  def checkCredentials(self, username, password):
    
    time.sleep(5) # TEMP: just to check login screen progress bar
    if self.usermanager.validate_user_login(username, password):
      user_settings = self.usermanager.get_user(username)
    else:
      return False
  
  @wamp.register(u'liestudio.config.retrieve')
  def retrievePassword(self, email):
    return self.usermanager.retrieve_password(email)
  
  @inlineCallbacks
  def onJoin(self, details):
    res = yield self.register(self)
    logger.debug("UserBackend: {} procedures registered!".format(len(res)))

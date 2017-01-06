# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

from   autobahn import wamp
from   pymongo import MongoClient
from   twisted.logger import LogLevel
from   twisted.internet.defer import inlineCallbacks

from   lie_system  import LieApplicationSession
from   settings import settings

class LoggerWampApi(LieApplicationSession):
    """
    Logger management WAMP methods.
    """
    db = None#MongoClient(host='localhost', port=27017)client['liestudio']
    log_collection = None#

    def __init__(self, config, package_config=None, **kwargs):

        super(LoggerWampApi, self).__init__(config, package_config, **kwargs)

        self.db = MongoClient(host=config.get('lie_db.host'), port=config.get('lie_db.port'))['liestudio']
        self.log_collection = self.db['log']

    @wamp.register(u'liestudio.logger.log')
    def log_event(self, event, default_log_level='info'):
        """
        Receive structured log events over WAMP and broadcast
        to local Twisted logger observers.

        :param event: Structured log event
        :type event:  dict
        :return:      standard return
        :rtype:       dict to JSON
        """
        
        log_level = LogLevel.levelWithName(event.get('log_level', default_log_level))
        self.log.emit(log_level, event.get('log_format', None), **event)
    
    @wamp.register(u'liestudio.logger.get')
    def get_log_events(self, user):
        """
        Retrieve structured log events from the database
        """
        
        posts = []
        for post in self.log_collection.find({"authid": user}, {'_id': False}):
            posts.append(post)
        
        return posts

def make(config):
    """
    Component factory
  
    This component factory creates instances of the application component
    to run.
    
    The function will get called either during development using an 
    ApplicationRunner, or as a plugin hosted in a WAMPlet container such as
    a Crossbar.io worker.
    The LieApplicationSession class is initiated with an instance of the
    ComponentConfig class by default but any class specific keyword arguments
    can be consument as well to populate the class session_config and
    package_config dictionaries.
    
    :param config: Autobahn ComponentConfig object
    """
    
    if config:
        return LoggerWampApi(config, package_config=settings)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio logging WAMPlet',
                'description': 'WAMPlet proving LIEStudio logging endpoint'}
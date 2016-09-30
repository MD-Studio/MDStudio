# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""

from   autobahn import wamp
from   autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from   pymongo import MongoClient
from   twisted.logger import Logger, LogLevel
from   twisted.internet.defer import inlineCallbacks

class LoggerWampApi(ApplicationSession):
    """
    Logger management WAMP methods.
    """
    logging = Logger()

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        
        client = MongoClient(host='localhost', port=27017)
        db = client['liestudio']
        self.log = db['log']
    
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
        self.logging.emit(log_level, event.get('log_format', None), **event)
    
    @wamp.register(u'liestudio.logger.get')
    def get_log_events(self, user):
        """
        Retrieve structured log events from the database
        """
        
        posts = []
        for post in self.log.find({"lie_user": user}, {'_id': False}):
            posts.append(post)
        
        return posts
        
    @inlineCallbacks
    def onJoin(self, details):
        res = yield self.register(self)
        self.logging.debug("{0}: {1} procedures registered!".format(self.__class__.__name__, len(res)))

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
        return LoggerWampApi(config)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio logging WAMPlet',
                'description': 'WAMPlet proving LIEStudio logging endpoint'}

if __name__ == '__main__':
    
    # test drive the component during development ..
    runner = ApplicationRunner(
        url="wss://localhost:8083/ws",
        realm="liestudio")  # app-level debugging

    runner.run(make)

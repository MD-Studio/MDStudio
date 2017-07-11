# -*- coding: utf-8 -*-

"""
file: wamp_services.py

WAMP service methods the module exposes.
"""
import re

from autobahn                import wamp
from autobahn.wamp.exception import ApplicationError
from twisted.internet.defer  import inlineCallbacks, returnValue

from lie_componentbase import BaseApplicationSession

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
    "authenticator": [
        {
            "uri": u"liestudio.user",
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
            "uri": u"liestudio.db",
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
    ],
    "admin": [
        {
            "uri": u"",
            "match": "prefix",
            "allow": {
                "call": True,
                "register": True,
                "publish": True,
                "subscribe": True
            },
            "disclose": {
                "caller": False,
                "publisher": False
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
        

class AuthorizerWampApi(BaseApplicationSession):
    """
    User management WAMP methods.
    """
    
    def preInit(self, **kwargs):
        self.session_config_template = {}

    @wamp.register(u'liestudio.authorizer.authorize')
    @inlineCallbacks
    def authorize(self, session, uri, action, options, details=None):
        role = session.get('authrole')

        if role in PERMISSIONS.keys():
            for rule in PERMISSIONS[role]:
                rulematch = False
                if 'match' in rule.keys():
                    if rule['match'] == 'prefix' and uri.startswith('{}.'.format(rule['uri'])):
                        rulematch = True
                    elif rule['match'] == 'exact' and uri == rule['uri']:
                        rulematch = True
                
                if rulematch:
                    permission = extract_permission(rule, uri, action)
                    self.log.debug( 'DEBUG: found matching rule {}, permission is: {}'.format(rule, permission))
                    returnValue(permission)
                    
        if session.get('authprovider') is None and role in ('authorizer', 'authenticator', 'schema', 'db'):
            authid = role
        else:
            authid = session.get('authid')
            namespaces = yield self.call(u'liestudio.user.namespaces', {'username': authid})

            if namespaces and any([uri.startswith('liestudio.{}.'.format(namespace)) for namespace in namespaces]):
                self.log.debug('DEBUG: authorizing {} to perform {} on {}'.format(authid, action, uri))
                returnValue({'allow': True})

        self.log.debug( 'DEBUG: authid resoved to {}'.format(authid))
        if authid and action == 'call' and (uri.startswith('liestudio.db.') or uri == 'liestudio.schema.register'):
            self.log.debug('DEBUG: authorizing {} to perform {} on {}'.format(authid, action, uri))
            returnValue({ 'allow': True, 'disclose': True })

        if action == 'call' and re.match('liestudio.schema.get', uri):
            self.log.debug('DEBUG: authorizing {} to perform {} on {}'.format(authid, action, uri))
            returnValue({'allow': True})

        if action == 'call' and uri == u'liestudio.user.logout':
            returnValue({'allow': True, 'disclose': True})

        self.log.warn('WARNING: {} is not authorized for {} on {}'.format(authid, action, uri))

        returnValue(False)
        

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
        return AuthorizerWampApi(config, package_config=SETTINGS)
    else:
        # if no config given, return a description of this WAMPlet ..
        return {'label': 'LIEStudio user management WAMPlet',
                'description': 'WAMPlet proving LIEStudio user management endpoints'}
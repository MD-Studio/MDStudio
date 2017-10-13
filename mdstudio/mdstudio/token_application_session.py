# coding=utf-8
from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock


class TokenApplicationSession(ApplicationSession):
    def __init__(self, config, **kwargs):
        # Init toplevel ApplicationSession
        super(TokenApplicationSession, self).__init__(config)

        self.oauth_token = config.extra['oauth_token']
        self.operation = config.extra['operation']

    def onConnect(self):
        # Establish transport layer
        self.join(self.config.realm, authmethods=[u'ticket'], authid=u'lieadmin')

    def onChallenge(self, challenge):
        # WAMP-Ticket based authentication
        if challenge.method == u"ticket":
            return self.oauth_token

    @inlineCallbacks
    def onJoin(self, details):
        self.operation.callback(self)
        yield self.operation
        self.leave()

    def onLeave(self, details):
        pass

import base64
import binascii
import json

from autobahn.wamp.auth import create_authenticator, AuthScram
from autobahn.wamp.message import Challenge
from passlib.utils import saslprep
from mdstudio.api.scram import SCRAM
from mdstudio.cache.impl.connection import GlobalCache
from mdstudio.component.impl.common import CommonSession
from mdstudio.db.connection_type import ConnectionType
from mdstudio.db.impl.connection import GlobalConnection
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.session import GlobalSession


class ComponentSession(CommonSession):
    # type: IDatabase
    db = None

    def on_connect(self):
        auth_methods = [u'scram']
        auth_role = u'user'
        authid = u'{}'.format(self.component_config.session.username)
        password = u'{}'.format(self.component_config.session.password)
        self.authenticator = create_authenticator(AuthScram.name, authid=authid, password=saslprep(password))

        # self.join(self.config.realm, authmethods=auth_methods, authid=authid, authrole=auth_role, authextra=self.authenticator.authextra)
        self.join(self.config.realm, [u'ticket'], authid, u'user')

    onConnect = on_connect

    def on_challenge(self, challenge):
        # challenge.extra['salt'] = challenge.extra['salt'].encode('ascii')
        # return self.authenticator.on_challenge(self, challenge)
        password = u'{}'.format(self.component_config.session.password)
        return password

    onChallenge = on_challenge

    def on_welcome(self, welcome):
        # return self.authenticator.on_welcome(self, welcome.authextra)
        pass

    onWelcome = on_welcome

    @chainable
    def on_join(self):
        yield super(ComponentSession, self).on_join()

        # notify that this is our session
        GlobalSession(self)

        self.db = GlobalConnection.get_wrapper(ConnectionType.User)
        self.cache = GlobalCache.get_wrapper(ConnectionType.User)

    def flush_logs(self, logs):
        return self.default_call_context.call(u'mdstudio.logger.endpoint.push-logs', {'logs': logs}, self.default_call_context.get_log_claims())

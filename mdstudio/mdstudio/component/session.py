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
        self.authenticator = create_authenticator(AuthScram.name, authid=self.component_config.session.username, password=saslprep(u'{}'.format(self.component_config.session.password)))

        self.join(self.config.realm, authmethods=auth_methods, authid=self.component_config.session.username, authrole=auth_role, authextra=self.authenticator.authextra)

    onConnect = on_connect

    def on_challenge(self, challenge):
        challenge.extra['salt'] = challenge.extra['salt'].encode('ascii')
        return self.authenticator.on_challenge(self, challenge)

    onChallenge = on_challenge

    def on_welcome(self, welcome):
        return self.authenticator.on_welcome(self, welcome.authextra)

    onWelcome = on_welcome

    @chainable
    def on_join(self):
        yield super(ComponentSession, self).on_join()

        # notify that this is our session
        GlobalSession(self)

        self.db = GlobalConnection.get_wrapper(ConnectionType.User)
        self.cache = GlobalCache.get_wrapper(ConnectionType.User)

    @chainable
    def flush_logs(self, logs):
        with self.default_context() as c:
            result = yield self.call(u'mdstudio.logger.endpoint.push-logs', {'logs': logs}, c.get('call_context').get_log_claims())

        return_value(result)

from mdstudio.component.impl.common import CommonSession
from mdstudio.db.connection import ConnectionType
from mdstudio.db.database import IDatabase
from mdstudio.db.impl.connection import GlobalConnection
from mdstudio.deferred.chainable import chainable


class ComponentSession(CommonSession):
    # type: IDatabase
    db = None

    def on_connect(self):
        auth_methods = ['ticket']
        authid = self.component_config.session.username
        auth_role = 'oauthclient'

        self.join(self.config.realm, authmethods=auth_methods, authid=authid, authrole=auth_role)

    onConnect = on_connect

    def on_challenge(self):
        return self.component_config.session.password

    onChallenge = on_challenge

    @chainable
    def on_join(self):
        yield super(ComponentSession, self).on_join()
        self.db = GlobalConnection(self).get_wrapper(ConnectionType.User)

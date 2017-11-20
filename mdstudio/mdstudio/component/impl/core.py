from autobahn.wamp import auth

from mdstudio.component.impl.common import CommonSession
from mdstudio.deferred.chainable import chainable
from mdstudio.logging.log_type import LogType
from mdstudio.logging.impl.session_observer import SessionLogObserver


class CoreComponentSession(CommonSession):
    def pre_init(self):
        self.log_type = LogType.Group

    def on_connect(self):
        auth_methods = [u'wampcra']
        authid = self.component_config.session.username
        auth_role = authid

        self.join(self.config.realm, authmethods=auth_methods, authid=authid, authrole=auth_role)

    onConnect = on_connect

    def on_challenge(self, challenge):
        if challenge.method == u'wampcra':
            # Salted password
            if u'salt' in challenge.extra:
                key = auth.derive_key(self.component_config.session.authid, challenge.extra['salt'],
                                      challenge.extra['iterations'], challenge.extra['keylen'])
            else:
                key = self.component_config.session.username

            return auth.compute_wcs(key.encode('utf8'), challenge.extra['challenge'].encode('utf8'))
        else:
            raise Exception("Core components should only use wampcra for authentication, attempted to use {}".format(challenge.method))

    onChallenge = on_challenge

    def load_settings(self):
        self.component_config.session['username'] = self.class_name.lower().replace('component', '', 1)
        self.component_config.static['vendor'] = 'mdstudio'
        self.component_config.static['component'] = self.component_config.session.username

        super(CoreComponentSession, self).load_settings()

    def flush_logs(self, logs):
        return self.call(u'mdstudio.logger.endpoint.log', {'logs': logs}, claims={'logType': str(LogType.Group), 'group': 'mdstudio'})

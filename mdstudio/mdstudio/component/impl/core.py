from autobahn.wamp import auth

from mdstudio.component.impl.common import CommonSession

class CoreComponentSession(CommonSession):
    def __init__(self, config = None):
        super(CoreComponentSession, self).__init__(config)

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
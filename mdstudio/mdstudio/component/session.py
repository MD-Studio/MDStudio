from mdstudio.component.impl.common import CommonSession


class ComponentSession(CommonSession):

    def on_connect(self):
        auth_methods = ['ticket']
        authid = self.component_config.session.username
        auth_role = 'oauthclient'

        self.join(self.config.realm, authmethods=auth_methods, authid=authid, authrole=auth_role)

    onConnect = on_connect

    def on_challenge(self):
        return self.component_config.session.password

    onChallenge = on_challenge
class OAuthClient:
    def __init__(self, userId=None, grantType=None, responseType=None, scope=None, redirectUris=None, clientId=None, secret=None, **kwargs):
        self.user_id = userId
        self.grant_type = grantType
        self.response_type = responseType
        self.scope = scope
        self.redirect_uris = redirectUris
        self.client_id = clientId
        self.secret = secret

    def __str__(self):
        return '<OAuthClient [{}]>'.format(self.__dict__.items())
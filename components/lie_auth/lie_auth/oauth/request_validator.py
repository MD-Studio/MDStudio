import datetime
import copy
import pytz
import re

from dateutil.parser import parse as parsedate
from twisted.internet.defer import inlineCallbacks, returnValue
from oauthlib import oauth2
from oauthlib import common

from mdstudio.db.model import Model

from .client import OAuthClient

# TODO: WebApplicationClient, BackendApplicationClient
class OAuthRequestValidator(oauth2.RequestValidator):
    def __init__(self, session):
        self.session = session

    def authenticate_client(self, request, *args, **kwargs):
        credentials = request.extra_credentials['http_basic']

        if credentials and credentials == request.headers['Authorization']:
            request.client = OAuthClient(**request.extra_credentials['client'])
            return True

        return False

    # def authenticate_client_id(self, client_id, request, *args, **kwargs):
    #     # again, check session
    #     return False

    # def client_authentication_required(self, request, *args, **kwargs):
    #     return True

    # def confirm_redirect_uri(self, code, redirect_uri, client, *args, **kwargs):
    #     return False

    # def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
    #     return u'mdstudio.schemas.get'

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        return oauth2.rfc6749.utils.scope_to_list(request.client.scope)

    # def get_original_scopes(self, refresh_token, request, *args, **kwargs):
    #     return []

    # def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
    #     raise Exception

    # def is_within_original_scope(self, request_scopes, refresh_token, request, *args, **kwargs):
    #     return False

    # def revoke_token(self, token, token_type, request, *args, **kwargs):
    #     raise Exception

    # def rotate_refresh_token(self, request):
    #     return True

    # def save_authorization_code(self, client_id, code, request, *args, **kwargs):
    #     raise Exception

    def save_bearer_token(self, token, request, *args, **kwargs):
        if token['token_type'] == 'Bearer':
            token.pop('http_basic')
            token.pop('token_type')
            client = token.pop('client')
            token['clientId'] = client['clientId']
            token['accessToken'] = token.pop('access_token')
            token['expirationTime'] = (datetime.datetime.now(pytz.utc) + datetime.timedelta(seconds=token.pop('expires_in'))).isoformat()

            Model(self.session, 'tokens').insert_one(copy.deepcopy(token), date_fields=['insert.expirationTime'])
        else:
            raise NotImplementedError('Subclasses has not implemented this path.')

    @inlineCallbacks
    def validate_bearer_token(self, token, scopes, request):
        if not token:
            returnValue(False)

        bearer = yield Model(self.session, 'tokens').find_one({'accessToken': token})

        if not bearer:
            returnValue(False)


        if datetime.datetime.now(pytz.utc) > datetime.datetime.fromtimestamp(parsedate(bearer['expirationTime']).timestamp(), tz=pytz.utc):
            returnValue(False)

        for scope in oauth2.rfc6749.utils.scope_to_list(bearer['scope']):
            if scope in scopes:
                returnValue(True)

        returnValue(False)

    # def validate_client_id(self, client_id, request, *args, **kwargs):
    #     return False

    # def validate_code(self, client_id, code, client, request, *args, **kwargs):
    #     return False

    def validate_grant_type(self, client_id, grant_type, client, *args, **kwargs):
        return client.grant_type == grant_type

    # def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
    #     return False

    # def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
    #     return False

    # def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
    #     return False

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        valid = True

        client_scopes = oauth2.rfc6749.utils.scope_to_list(client.scope)

        for scope in scopes:
            if scope in client_scopes:
                continue

            match = re.match('(.*):(.*)', scope)

            if match and '{}:*'.format(match.group(1)) in client_scopes:
                continue

            # TODO: check for named scopes
            valid = False
            break
        
        return valid
    
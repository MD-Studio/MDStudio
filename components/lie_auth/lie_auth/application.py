# -*- coding: utf-8 -*-
import datetime
import json

import base64
import copy
from autobahn import wamp
from autobahn.wamp.exception import ApplicationError
from jwt import encode as jwt_encode, decode as jwt_decode, DecodeError, ExpiredSignatureError
from lie_auth.user_repository import UserRepository
from oauthlib import oauth2
from oauthlib.common import generate_client_id as generate_secret
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

from mdstudio.component.impl.core import CoreComponentSession
from mdstudio.deferred.chainable import chainable

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from mdstudio.api.register import register
from mdstudio.utc import now
from mdstudio.db.model import Model
from .oauth.request_validator import OAuthRequestValidator
from .authorizer import Authorizer


class AuthComponent(CoreComponentSession):
    def pre_init(self):
        self.oauth_client = oauth2.BackendApplicationClient('auth')
        self.component_waiters.append(CoreComponentSession.ComponentWaiter(self, 'db'))
        self.component_waiters.append(CoreComponentSession.ComponentWaiter(self, 'schema'))
        self.status_list = {'auth': True}

    def on_init(self):
        self.db_initialized = False
        self.authorizer = Authorizer()

    def onInit(self, **kwargs):
        self.oauth_backend_server = oauth2.BackendApplicationServer(OAuthRequestValidator(self))

        self.autolog = False
        self.autoschema = False

        # TODO: check this before accessing the DB


        # # TODO: make this a dict of  {vendor}.{namespace}: [urilist] for faster lookup
        # self.registrations = []

    @chainable
    def _on_join(self):
        self.jwt_key = generate_secret()
        yield super(AuthComponent, self)._on_join()

    @wamp.register(u'mdstudio.auth.endpoint.sign', options=wamp.RegisterOptions(details_arg='details'))
    def sign_claims(self, claims, details=None):
        role = details.caller_authrole

        if not isinstance(claims, dict):
            raise TypeError()

        if role in ['db', 'schema', 'auth', 'logger']:
            claims['groups'] = ['mdstudio']
            claims['username'] = role
        else:
            raise NotImplementedError("Implement this")

        claims['exp'] = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

        return jwt_encode(claims, self.jwt_key)

    @wamp.register(u'mdstudio.auth.endpoint.verify')
    def verify_claims(self, signed_claims):
        try:
            claims = jwt_decode(signed_claims, self.jwt_key)
        except DecodeError:
            return {'error': 'Could not verify user'}
        except ExpiredSignatureError:
            return {'expired': 'Request token has expired'}

        return {'claims': claims}

    @register('mdstudio.auth.endpoint.ring0.set-status', {}, {})
    def ring0_set_status(self, request, claims=None):
        self.status_list[claims['username']] = request['status']

    @register('mdstudio.auth.endpoint.ring0.get-status', {}, {})
    def ring0_get_status(self, request, claims=None):
        return self.status_list.get(request['component'], False)

    def authorize_request(self, uri, claims):
        if 'mdstudio' in claims['groups'] and uri.startswith('mdstudio.auth.endpoint.ring0'):
            return True

        return False

    @wamp.register(u'mdstudio.auth.endpoint.login')
    @inlineCallbacks
    def user_login(self, realm, authid, details):
        assert authid
        authmethod = details.get(u'authmethod', None)

        self.log.info('WAMP authentication request for realm: {realm}, authid: {authid}, method: {authmethod}}',
                      realm=realm, authid=authid, authmethod=authmethod)

        username = authid.strip()
        user = yield self._get_user(username)

        # WAMP-ticket authetication
        if authmethod == u'ticket':
            is_valid = self._validate_user_login(user, username, details['ticket'])
            if is_valid:
                auth_ticket = {u'realm': realm, u'role': user['role'], u'extra': self._strip_unsafe_properties(user)}
            else:
                # Not a valid user, try  to find a matching client
                client = yield self._get_client(username)
                if client:
                    client['scope'] = ' '.join(client.pop('scopes'))
                    http_basic = self._http_basic_authentication(username, details['ticket'])
                    credentials = {u'client': client,
                                   u'http_basic': self._http_basic_authentication(client[u'clientId'], client[u'secret'])}

                    headers, body, status = self.oauth_backend_server.create_token_response(
                        u'mdstudio.auth.endpoint.login',
                        headers={u'Authorization': http_basic},
                        grant_type_for_scope=u'client_credentials',
                        credentials=credentials)

                    if status == 200:
                        user = {u'_id': client[u'_id']}
                        auth_ticket = {u'realm': realm, u'role': 'oauthclient', u'extra': {u'access_token': json.loads(body).get('accessToken')}}
                    else:
                        raise ApplicationError("com.example.invalid_ticket", "could not authenticate session")
                else:
                    raise ApplicationError("com.example.invalid_ticket", "could not authenticate session")

        # WAMP-CRA authentication
        elif authmethod == u'wampcra':
            if user:
                auth_ticket = {u'realm': realm, u'role': user['role'], u'extra': self._strip_unsafe_properties(user),
                               u'secret': user[u'password']}
            else:
                raise ApplicationError("com.example.invalid_ticket", "could not authenticate session")

        else:
            raise ApplicationError("No such authentication method known: {0}".format(authmethod))

        yield self._start_session(user[u'_id'], details.get(u'session', 0), auth_ticket[u'extra'].get('access_token'))

        # Log authorization
        self.log.info('Access granted. user: {user}', user=authid)

        returnValue(auth_ticket)

    @chainable
    def on_run(self):
        repo = UserRepository(self.db)
        user = None
        group = None
        # try:
        yield repo.users.delete_many({})
        yield repo.groups.delete_many({})
        user = yield repo.create_user('foo', 'bar', 'foo@bar')
        user2 = yield repo.create_user('foo2', 'bar2', 'foo@bar')
        group = yield repo.create_group('foogroup', owner_username='foo')
        group_role = yield repo.create_group_role('foogroup', 'editor', user['handle'])
        added_member = yield repo.add_group_member('foogroup', group_role['handle'], user2['handle'])
        # finally:
        #     if group:
        #         yield repo.groups.delete_one({'groupName': 'foogroup'})
        #     if user:
        #         yield repo.users.delete_one({'username': 'foo'})

    # @register(u'mdstudio.auth.endpoint.oauth.registerscopes', {}, {}, match='prefix')
    # @inlineCallbacks
    # def register_scopes(self, request, **kwargs):
    #     for scope in request['scopes']:
    #         # update/insert the uri scope
    #         yield Model(self, 'scopes').update_one(scope, {'$set': scope}, True)
    #
    #     returnValue(None)

    @wamp.register(u'mdstudio.auth.endpoint.authorize.admin')
    def authorize_admin(self, session, uri, action, options):
        role = session.get('authrole')
        authid = session.get('authid')

        authorization = False

        if action in ('call', 'subscribe', 'publish'):
            # Allow admin to call, subscribe and publish on any uri
            # TODO: possibly restrict this
            authorization = {'allow': True}

        if not authorization:
            self.log.warn('WARNING: {} is not authorized for {} on {}'.format(authid, action, uri))
        else:
            if 'disclose' not in authorization:
                authorization['disclose'] = False

            if uri.startswith('mdstudio.auth.endpoint.oauth'):
                authorization['disclose'] = True

            self._store_action(uri, action, options)

        return authorization

    @wamp.register(u'mdstudio.auth.endpoint.authorize.ring0')
    def authorize_ring0(self, session, uri, action, options):
        role = session.get('authrole')

        authorization = self.authorizer.authorize_ring0(uri, action, role)

        if not authorization:
            self.log.warn('WARNING: {} is not authorized for {} on {}'.format(role, action, uri))
        else:
            if 'disclose' not in authorization:
                authorization['disclose'] = False

            self._store_action(uri, action, options)

        return authorization


    @wamp.register(u'mdstudio.auth.endpoint.authorize.oauth')
    @inlineCallbacks
    def authorize_oauth(self, session, uri, action, options):
        role = session.get('authrole')

        authid = session.get('authid')

        authorization = False

        client = yield self._get_client(authid)
        session = yield self._get_session(session.get('session'))
        scopes = self.authorizer.oauthclient_scopes(uri, action, authid)

        headers = {'access_token': session['accessToken']}
        valid, r = self.oauth_backend_server.verify_request(uri, headers=headers, scopes=[scope for scope in scopes])

        valid = yield valid

        if valid:
            authorization = {'allow': True}

        if not authorization:
            self.log.warn('WARNING: {} is not authorized for {} on {}'.format(authid, action, uri))
        else:
            if 'disclose' not in authorization:
                authorization['disclose'] = False

            self._store_action(uri, action, options)

        returnValue(authorization)

    @wamp.register(u'mdstudio.auth.endpoint.authorize.public')
    def authorize_public(self, session, uri, action, options):
        #  TODO: authorize public to view unprotected resources
        authorization = False

        returnValue(authorization)

    @wamp.register(u'mdstudio.auth.endpoint.authorize.user')
    def authorize_user(self, session, uri, action, options):
        # TODO: authorize users to view (parts of) the web interface and to create OAuth clients on their group/user
        authorization = False

        returnValue(authorization)

    @register(u'mdstudio.auth.endpoint.oauth.client.create', 'oauth/client/client-request', 'oauth/client/client-response')
    @inlineCallbacks
    def create_oauth_client(self, request, details=None):
        user = yield self._get_user(details.caller_authid)

        # TODO: check if user is permitted to access the requested scopes before creating the client
        clientInfo = copy.deepcopy(request)
        clientInfo['userId'] = user['_id']
        clientInfo['clientId'] = generate_secret()
        clientInfo['secret'] = generate_secret()

        yield Model(self, 'clients').insert_one(clientInfo)

        returnValue({
            'id': clientInfo['clientId'],
            'secret': clientInfo['secret']
        })

    @register(u'mdstudio.auth.endpoint.oauth.client.getusername', {}, {})
    @inlineCallbacks
    def get_oauth_client_username(self, request):
        client = yield self._get_client(request['clientId'])

        if client:
            user = yield self._get_user({'_id': client['userId']})

            returnValue({'username': user['username']})
        else:
            returnValue({})

    @wamp.register(u'mdstudio.auth.endpoint.logout', options=wamp.RegisterOptions(details_arg='details'))
    @inlineCallbacks
    def user_logout(self, details):
        user = yield self._get_user(details.get('authid'))
        if user:
            self.log.info('Logout user: {0}, id: {1}'.format(user['username'], user['_id']))

            ended = yield self._end_session(user['uid'], details.get('session'))
            if ended:
                returnValue('{0} you are now logged out'.format(user['username']))

        returnValue('Unknown user, unable to logout')


    # # TODO: improve and register this method, with json schemas
    # @inlineCallbacks
    # def create_user(self, userdata, required=['username', 'email']):
    #     """
    #     Create new user and add to database
    #     """
    #
    #
    #     # TODO: handle the following section with json schema
    #     # ----------------------------------------------------------------------------
    #     user_template = copy.copy(USER_TEMPLATE)
    #
    #     # Require at least a valid username and email
    #     for param in required:
    #         if not userdata.get(param, None):
    #             self.log.error('Unable to create new user. Missing "{0}"'.format(param))
    #             returnValue({})
    #
    #     # If no password, create random one
    #     if not userdata.get('password', None):
    #         random_pw = generate_password()
    #         user_template['password'] = hash_password(random_pw)
    #
    #     user_template.update(userdata)
    #     # ----------------------------------------------------------------------------
    #
    #     # Username and email should not be in use
    #     user = yield self._get_user(userdata['username'])
    #     if user:
    #         self.log.error('Username {0} already in use'.format(userdata['username']))
    #         returnValue({})
    #
    #     user = yield self._get_user({'email': userdata['email']})
    #     if user:
    #         self.log.error('Email {0} already in use'.format(userdata['email']))
    #         returnValue({})
    #
    #     # Add the new user to the database
    #     result = yield Model(self, 'users').insert_one(user_template)
    #     if result:
    #         self.log.debug('Added new user. user: {username}, id: {id}', id=result, **user_template)
    #     else:
    #         self.log.error('Unable to add new user to database')
    #         returnValue({})
    #
    #     returnValue(user_template)

    # # TODO: expose and secure this
    # def remove_user(self, userdata):
    #     """
    #     Remove a user from the database
    #
    #     :param userdata: PyMongo style database query
    #     :type userdata:  :py:class:`dict`
    #     """
    #
    #     user = self.get_user(userdata)
    #     if not user:
    #         self.log.error('No such user to remove: {0}'.format(
    #             ' '.join(['{0},{1}'.format(*item) for item in userdata.items()])))
    #         return False
    #     else:
    #         self.log.info('Removing user "{username}", with uid {uid} from database'.format(**user))
    #         db['users'].delete_one(user)
    #
    #     return True

    def _validate_user_login(self, user, username, password):
        """
        Validate login attempt for user with password

        :param username: username to check
        :type username:  string
        :param password: password to check
        :type password:  string
        :rtype:          bool
        """

        password = password.strip()

        check = False
        if user:
            check = check_password(user['password'], password)
        else:
            self.log.debug('No such user')

        self.log.info('{status} login attempt for user: {user}',
                      status='Correct' if check else 'Incorrect', user=username)

        return check

    def _http_basic_authentication(self, username, password):
        # mimic HTTP basic authentication
        # concatenate username and password with a colon
        http_basic = u'{}:{}'.format(username, password)
        # encode into an octet sequence (bytes)
        http_basic = http_basic.encode('utf_8')
        # encode in base64
        http_basic = base64.encodebytes(http_basic)

        return http_basic.decode('utf_8')

    @inlineCallbacks
    def _start_session(self, user_id, session_id, access_token):
        self.log.debug('Open session: {0} for user {1}'.format(session_id, user_id))
        res = yield Model(self, 'sessions').insert_one({'userId': user_id, 'sessionId': session_id, 'accessToken': access_token})
        returnValue(res)

    @inlineCallbacks
    def _get_session(self, session_id):
        res = yield Model(self, 'sessions').find_one({'sessionId': session_id})
        returnValue(res)

    @inlineCallbacks
    def _end_session(self, user_id, session_id):
        res = yield Model(self, 'sessions').delete_one({'userId': user_id, 'sessionId': session_id})
        returnValue(res > 0)

    def _store_action(self, uri, action, options):
        registration = Model(self, 'registration_info')

        n = now().isoformat()

        if action == 'register':
            match = options.get('match', 'exact')

            # @inlineCallbacks
            # def update_registration():
            #     upd = yield registration.update_one(
            #         {
            #             'uri': uri,
            #             'match': match
            #         },
            #         {
            #             '$inc': {
            #                 'registrationCount': 1
            #             },
            #             '$set': {
            #                 'latestRegistration': n
            #             },
            #             '$setOnInsert': {
            #                 'uri': uri,
            #                 'firstRegistration': n,
            #                 'match': match
            #             }
            #         },
            #         upsert=True,
            #         date_fields=['update.$set.latestRegistration', 'update.$setOnInsert.firstRegistration']
            #     )

            # We cannot be sure the DB is already up, possibly wait
            yield DBWaiter(self, update_registration).run()
        elif action == 'call':
            @inlineCallbacks
            def update_registration():
                id = yield self.call(u'wamp.registration.match', uri)
                if id:
                    reg_info = yield self.call(u'wamp.registration.get', id)
                    # yield registration.update_one(
                    #     {
                    #         'uri': reg_info['uri'],
                    #         'match': reg_info['match']
                    #     },
                    #     {
                    #         '$inc': {
                    #             'callCount': 1
                    #         },
                    #         '$set': {
                    #             'latestCall': now
                    #         }
                    #     },
                    #     date_fields=['update.$set.latestCall']
                    # )

            # We cannot be sure the DB is already up, possibly wait
            yield DBWaiter(self, update_registration).run()

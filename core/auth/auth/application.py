# -*- coding: utf-8 -*-
import base64
import copy
import datetime

from autobahn import wamp
from autobahn.wamp.exception import ApplicationError
from jwt import encode as jwt_encode, decode as jwt_decode, DecodeError, ExpiredSignatureError
from oauthlib import oauth2
from oauthlib.common import generate_client_id as generate_secret
from twisted.internet.defer import inlineCallbacks, returnValue

from auth.user_repository import UserRepository, PermissionType
from mdstudio.api.context import with_default_context
from mdstudio.api.endpoint import endpoint
from mdstudio.api.scram import SCRAM
from mdstudio.component.impl.core import CoreComponentSession
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from mdstudio.utc import now
from mdstudio.service.model import Model
from .oauth.request_validator import OAuthRequestValidator
from .authorizer import Authorizer


class AuthComponent(CoreComponentSession):
    def pre_init(self):
        self.oauth_client = oauth2.BackendApplicationClient('auth')
        self.component_waiters.append(CoreComponentSession.ComponentWaiter(self, 'db'))
        self.component_waiters.append(CoreComponentSession.ComponentWaiter(self, 'schema'))
        self.status_list = {'auth': True}
        super(AuthComponent, self).pre_init()

    def on_init(self):
        self.db_initialized = False
        self.authorizer = Authorizer()
        self.oauth_backend_server = oauth2.BackendApplicationServer(OAuthRequestValidator(self))
        self.user_repository = UserRepository(self.db)

    @chainable
    def _on_join(self):
        self.jwt_key = generate_secret()
        yield super(AuthComponent, self)._on_join()

    @wamp.register(u'mdstudio.auth.endpoint.sign', options=wamp.RegisterOptions(details_arg='details'))
    @with_default_context
    @chainable
    def sign_claims(self, claims, details=None):
        role = details.caller_authrole

        if not isinstance(claims, dict):
            raise TypeError()

        assert not any(key in claims for key in ['group', 'role', 'username']), 'Illegal key detected in claims'

        if 'asGroup' in claims:
            group = claims.pop('asGroup')

            if group is None:
                raise TypeError()
        else:
            group = None

        if 'asRole' in claims:
            assert group is not None, 'You cannot claim to be member of a role without the corresponding group'

            group_role = claims.pop('asRole')

            if group_role is None:
                raise TypeError()
        else:
            group_role = None

        if role in ['db', 'cache', 'schema', 'auth', 'logger']:
            claims['username'] = role

            if group is not None:
                if group == 'mdstudio':
                    claims['group'] = 'mdstudio'
                else:
                    raise Exception('This should not happen')

            if group_role is not None:
                if group_role == role:
                    claims['role'] = role
                else:
                    raise Exception('This should not happen: claimed to be {} but was {}'.format(group_role, role))
        elif role == 'user':
            user = yield self.user_repository.find_user(details.caller_authid)

            claims['username'] = user.name

            g, c, _, e = claims['uri'].split('.', 3)

            if group is not None:
                if self.authorizer.authorize_user(claims['uri'], claims['action']) or (
                        g == group and
                        (yield self.user_repository.check_permission(user.name, g, c, e, claims['action'], group_role))
                ):
                    claims['group'] = group

                    if group_role is not None:
                        claims['role'] = group_role
                else:
                    return_value(None)
        else:
            raise NotImplementedError('Implement this (for oauth clients)')

        claims['exp'] = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)

        return_value(jwt_encode(claims, self.jwt_key))

    @wamp.register(u'mdstudio.auth.endpoint.verify')
    @with_default_context
    def verify_claims(self, signed_claims):
        try:
            claims = jwt_decode(signed_claims, self.jwt_key)
        except DecodeError:
            return {'error': 'Could not verify user'}
        except ExpiredSignatureError:
            return {'expired': 'Request token has expired'}

        return {'claims': claims}

    @endpoint('ring0.set-status', {}, {})
    def ring0_set_status(self, request, claims=None):
        self.status_list[claims['username']] = request['status']

    @endpoint('ring0.get-status', {}, {})
    def ring0_get_status(self, request, claims=None):
        return self.status_list.get(request['component'], False)

    def authorize_request(self, uri, claims):
        if claims.get('group', None) == 'mdstudio' and uri.startswith('mdstudio.auth.endpoint.ring0'):
            return True

        return False

    @wamp.register(u'mdstudio.auth.endpoint.login')
    @with_default_context
    @inlineCallbacks
    def user_login(self, realm, authid, details):
        assert authid
        authmethod = details.get(u'authmethod', None)
        assert authmethod == u'wampcra', 'Only wampcra is supported for login, please use the ComponentSession'

        authid = authid.strip()
        username, client_nonce = SCRAM.split_authid(authid)
        server_nonce = details['session']

        self.log.info('WAMP authentication request for realm: {realm}, authid: {authid}, method: {authmethod}, phase: {authphase}', realm=realm, authid=username, authmethod=authmethod, authphase=details['authphase'])

        user = yield self.user_repository.find_user(username, with_authentication=True)

        if user is not None:
            user_auth = user.authentication
            stored_key = SCRAM.str_to_binary(user_auth['storedKey'])
            server_key = SCRAM.str_to_binary(user_auth['serverKey'])

            if details['authphase'] == 'preChallenge':
                auth_ticket = {
                    'role': 'user',
                    'iterations': user_auth['iterations'],
                    'salt': user_auth['salt'],
                    'secret': SCRAM.binary_to_str(stored_key)
                }
            else:
                auth_message = SCRAM.auth_message(client_nonce, server_nonce)
                client_signature = SCRAM.client_signature(stored_key, auth_message)
                client_proof = SCRAM.str_to_binary(details['signature'])
                client_key = SCRAM.client_proof(client_proof, client_signature)

                if SCRAM.stored_key(client_key) == stored_key:
                    auth_ticket = {
                        'authid': username,
                        'success': True,
                        'extra': {
                            'serverProof': SCRAM.binary_to_str(SCRAM.server_proof(server_key, auth_message))
                        }
                    }

                    # Log authorization
                    self.log.info('Access granted. user: {user}', user=username)
                else:
                    auth_ticket = False
        else:
            raise ApplicationError("No such user")

        returnValue(auth_ticket)

    @chainable
    def on_run(self):
        # repo = UserRepository(self.db)
        yield self.user_repository.users.delete_many({})
        yield self.user_repository.groups.delete_many({})
        provisioning = self.component_config.settings.get('provisioning', None)
        if provisioning is not None:
            for user in provisioning.get('users', []):
                u = yield self.user_repository.find_user(user['username'])
                if u is None:
                    salt, iterations, salted_password = SCRAM.salted_password(user['password'])
                    stored_key = SCRAM.stored_key(SCRAM.client_key(salted_password))
                    server_key = SCRAM.server_key(salted_password)

                    u = yield self.user_repository.create_user(user['username'], {
                        'storedKey': SCRAM.binary_to_str(stored_key),
                        'serverKey': SCRAM.binary_to_str(server_key),
                        'salt': salt,
                        'iterations': iterations
                    }, user['email'])
                assert u.name == user['username'], 'User provisioning for user {} changed. If intentional, clear the database.'.format(user['username'])
            for group in provisioning.get('groups', []):
                g = yield self.user_repository.find_group(group['groupName'])
                if g is None:
                    g = yield self.user_repository.create_group(group['groupName'], group['owner'])
                assert g.name == group['groupName']

                for component in group.get('components', []):
                    c = yield self.user_repository.find_component(g.name, component)
                    if c is None:
                        c = yield self.user_repository.create_component(g.name, 'owner', component)
                    assert c.name == component

                for component in ['auth', 'db', 'logger', 'schema']:
                    p = yield self.user_repository.find_permission_rule(g.name, 'owner', 'groupResourcePermission', component)
                    if p is None:
                        p = yield self.user_repository.add_permission_rule(g.name, 'owner', 'roleResourcePermissions', component, PermissionType.FullAccess, full_namespace=True)
                        assert p
                    else:
                        p = yield self.user_repository.find_permission_rule(g.name, 'owner', 'groupResourcePermission', component)
                        assert p.full_namespace
            '''for client in provisioning.get('clients', []):
                client_id = self.user_repository.generate_token()
                client_secret = self.user_repository.generate_token()

                c = yield self.user_repository.create_client(client['username'], {

                })'''

        # @todo: use this for testing
        # user = yield self.user_repository.create_user('foo', 'bar', 'foo@bar')
        # user2 = yield self.user_repository.create_user('foo2', 'bar2', 'foo@bar')
        # user3 = yield self.user_repository.create_user('foo3', 'bar2', 'foo@bar3')
        # group = yield self.user_repository.create_group('foogroup', user.name)
        # group_role = yield self.user_repository.create_group_role(group.name, 'editor', user.name)
        # group_role2 = yield self.user_repository.create_group_role(group.name, 'user', user.name)
        # group_role3 = yield self.user_repository.create_group_role(group.name, 'user2', user.name)
        # group_role4 = yield self.user_repository.create_group_role(group.name, 'user3', user.name)
        # group_role5 = yield self.user_repository.create_group_role(group.name, 'user4', user.name)
        # assert (yield self.user_repository.add_group_member(group.name, group_role.name, user2.name))
        # assert (yield self.user_repository.add_role_member(group.name, group_role2.name, user2.name))
        # assert (yield self.user_repository.add_group_member(group.name, group_role.name, user3.name))
        # component = (yield self.user_repository.create_component(group.name, group_role.name, 'foo'))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role2.name, 'componentPermissions', component.name, PermissionType.NamedScope, ['call', 'register'], 'read'))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role2.name, 'componentPermissions', component.name, PermissionType.NamedScope, ['call'], 'write'))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role2.name, 'componentPermissions', component.name, PermissionType.NamedScope, ['register'], 'write'))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role2.name, 'componentPermissions', component.name, PermissionType.SpecificEndpoint, ['register'], 'write'))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role2.name, 'componentPermissions', component.name, PermissionType.ComponentNamespace, ['register']))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role2.name, 'componentPermissions', component.name, PermissionType.ComponentNamespace, ['write']))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role2.name, 'componentPermissions', component.name, PermissionType.FullAccess, full_namespace=True))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role3.name, 'componentPermissions', component.name, PermissionType.SpecificEndpoint, ['register'], 'write'))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role4.name, 'componentPermissions', component.name, PermissionType.ComponentNamespace, ['register']))
        # assert (yield self.user_repository.add_permission_rule(group.name, group_role5.name, 'componentPermissions', component.name, PermissionType.FullAccess, full_namespace=True))

    # @todo: write a better replacement
    # @inlineCallbacks
    # def register_scopes(self, request, **kwargs):
    #     for scope in request['scopes']:
    #         # update/insert the uri scope
    #         yield Model(self, 'scopes').update_one(scope, {'$set': scope}, True)
    #
    #     returnValue(None)

    @wamp.register(u'mdstudio.auth.endpoint.authorize.admin')
    @with_default_context
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
    @with_default_context
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


    # @wamp.register(u'mdstudio.auth.endpoint.authorize.oauth')
    # @with_default_context
    # @inlineCallbacks
    # def authorize_oauth(self, session, uri, action, options):
    #     role = session.get('authrole')
    #
    #     authid = session.get('authid')
    #
    #     authorization = False
    #
    #     client = yield self._get_client(authid)
    #     session = yield self._get_session(session.get('session'))
    #     scopes = self.authorizer.oauthclient_scopes(uri, action, authid)
    #
    #     headers = {'access_token': session['accessToken']}
    #     valid, r = self.oauth_backend_server.verify_request(uri, headers=headers, scopes=[scope for scope in scopes])
    #
    #     valid = yield valid
    #
    #     if valid:
    #         authorization = {'allow': True}
    #
    #     if not authorization:
    #         self.log.warn('WARNING: {} is not authorized for {} on {}'.format(authid, action, uri))
    #     else:
    #         if 'disclose' not in authorization:
    #             authorization['disclose'] = False
    #
    #         self._store_action(uri, action, options)
    #
    #     returnValue(authorization)

    # @wamp.register(u'mdstudio.auth.endpoint.authorize.public')
    # @with_default_context
    # def authorize_public(self, session, uri, action, options):
    #     #  TODO: authorize public to view unprotected resources
    #     authorization = False
    #
    #     returnValue(authorization)

    @wamp.register(u'mdstudio.auth.endpoint.authorize.user')
    @with_default_context
    @chainable
    def authorize_user(self, session, uri, action, options):
        username = session.get('authid')

        # Check for authorization on ring0
        authorization = self.authorizer.authorize_user(uri, action)

        if not authorization:
            group, component, _, endpoint = uri.split('.', 3)
            if (yield self.user_repository.check_permission(username, group, component, endpoint, action)):
                authorization = {
                    'allow': True
                }

        if not authorization:
            self.log.warn('WARNING: {} is not authorized for {} on {}'.format(username, action, uri))
        else:
            if 'disclose' not in authorization:
                authorization['disclose'] = False

            self._store_action(uri, action, options)

        return_value(authorization)

    @endpoint('oauth.client.create', 'oauth/client/client-request', 'oauth/client/client-response')
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

    @endpoint('oauth.client.getusername', {}, {})
    @inlineCallbacks
    def get_oauth_client_username(self, request):
        client = yield self._get_client(request['clientId'])

        if client:
            user = yield self._get_user({'_id': client['userId']})

            returnValue({'username': user['username']})
        else:
            returnValue({})

    @wamp.register(u'mdstudio.auth.endpoint.logout', options=wamp.RegisterOptions(details_arg='details'))
    @with_default_context
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
